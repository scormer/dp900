import streamlit as st
import random
import os
import json

# --- Configuration Constants ---
MIN_QUESTION = 1
MAX_QUESTION = 177
# IMPORTANT: Ensure your 'AZ900' image folder is in the same directory as this Python script
IMAGE_FOLDER = 'DP900' 
# Directory to store user-specific data (e.g., skipped questions)
DATA_DIR = "user_data" 

# Create the data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Passcode for app access
APP_PASSCODE = "az900fun"

# --- Session State Initialization ---
# This function ensures all necessary state variables are initialized when the app starts
# or when a new session begins.
def initialize_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""
    if 'all_questions' not in st.session_state:
        # Create a list of all possible question numbers
        st.session_state.all_questions = list(range(MIN_QUESTION, MAX_QUESTION + 1))
    if 'current_playlist' not in st.session_state:
        st.session_state.current_playlist = []
    if 'playlist_index' not in st.session_state:
        st.session_state.playlist_index = 0
    if 'showing_answer' not in st.session_state:
        st.session_state.showing_answer = False
    if 'is_shuffled' not in st.session_state:
        st.session_state.is_shuffled = False
    if 'skipped_questions' not in st.session_state:
        # Use a set for efficient storage and lookup of skipped questions
        st.session_state.skipped_questions = set() 

# --- Persistence Functions ---

def get_user_data_file(username):
    """
    Constructs the file path for a user's skipped questions data.
    Sanitizes the username to create a valid filename.
    """
    # Simple sanitization: allow alphanumeric, spaces, dots, underscores
    safe_username = "".join(c for c in username if c.isalnum() or c in (' ', '.', '_')).strip()
    if not safe_username:
        return None # Return None if username is empty after sanitization
    return os.path.join(DATA_DIR, f"{safe_username}_skipped.json")

def save_skipped_questions(username, skipped_set):
    """
    Saves the set of skipped questions for a given user to a JSON file.
    """
    file_path = get_user_data_file(username)
    if file_path:
        try:
            # Convert set to list for JSON serialization
            with open(file_path, 'w') as f:
                json.dump(list(skipped_set), f) 
            st.toast(f"Skipped questions saved for {username}!")
        except Exception as e:
            st.error(f"Error saving data for {username}: {e}")

def load_skipped_questions(username):
    """
    Loads skipped questions for a given user from their JSON file.
    Handles file not found or corrupted file cases.
    """
    file_path = get_user_data_file(username)
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                loaded_list = json.load(f)
                return set(loaded_list) # Convert list back to set
        except json.JSONDecodeError:
            st.warning("Skipped questions file is corrupted, starting fresh.")
            return set()
        except Exception as e:
            st.error(f"Error loading data for {username}: {e}")
            return set()
    return set() # Return an empty set if file doesn't exist or no username

# --- Core Flashcard Logic Functions ---

def shuffle_array(array):
    """Shuffles an array in place using random.shuffle."""
    random.shuffle(array)
    return array

def build_playlist():
    """
    Builds the current playlist based on the shuffle mode and excluded skipped questions.
    Resets the playlist index and showing_answer state.
    """
    # Filter out questions that are in the skipped_questions set
    available_questions = [q for q in st.session_state.all_questions if q not in st.session_state.skipped_questions]

    if st.session_state.is_shuffled:
        st.session_state.current_playlist = shuffle_array(available_questions)
    else:
        # Sort for sequential order
        st.session_state.current_playlist = sorted(available_questions) 

    st.session_state.playlist_index = 0 # Always reset index when playlist is rebuilt
    st.session_state.showing_answer = False # Always show question first
    
    if not st.session_state.current_playlist:
        st.warning("No questions available based on current skipped list. Try clearing the skipped list.")

def update_flashcard_image():
    """
    Displays the current flashcard image (question or answer) using st.image.
    Handles cases where no questions are in the playlist or image files are missing.
    """
    if not st.session_state.current_playlist:
        st.image("https://placehold.co/800x400/cccccc/333333?text=No+Questions+Available", caption="No questions to display.", use_container_width=True)
        return

    current_q_num = st.session_state.current_playlist[st.session_state.playlist_index]
    image_type = 'A' if st.session_state.showing_answer else 'Q'
    # Format the question number with leading zeros (e.g., 1 -> 001)
    image_filename = f"{image_type}_{str(current_q_num).zfill(3)}.png" 
    image_path = os.path.join(IMAGE_FOLDER, image_filename)

    if os.path.exists(image_path):
        st.image(image_path, caption=f"Question {current_q_num}", use_container_width=True)
    else:
        st.warning(f"Image not found for Q{current_q_num}: {image_path}. Please ensure images are in the '{IMAGE_FOLDER}' folder.")
        # Fallback placeholder image
        st.image("https://placehold.co/800x400/ffcc00/000000?text=Image+Missing", caption=f"Image for Q{current_q_num} missing", use_container_width=True)

def go_to_playlist_index(index):
    """
    Navigates to a specific index within the `current_playlist`.
    Updates the `playlist_index` and resets `showing_answer`.
    """
    if not st.session_state.current_playlist:
        st.warning("No questions in the playlist.")
        return

    if 0 <= index < len(st.session_state.current_playlist):
        st.session_state.playlist_index = index
        st.session_state.showing_answer = False # Always show question first when navigating
    else:
        st.info("End of playlist reached.")

def go_to_question_by_number():
    """
    Handles navigation to a specific question number entered by the user.
    Triggered by the `on_change` event of the question number input.
    """
    q_num_str = st.session_state.question_num_input # Get value from session state
    try:
        q_num = int(q_num_str)
        if not (MIN_QUESTION <= q_num <= MAX_QUESTION):
            st.error(f"Please enter a number between {MIN_QUESTION} and {MAX_QUESTION}.")
            return
        
        # Check if the entered question is in the skipped list
        if q_num in st.session_state.skipped_questions:
            st.session_state.skipped_questions.remove(q_num) # Remove from skipped list
            build_playlist() # Rebuild playlist to include this question
            if st.session_state.user_name:
                save_skipped_questions(st.session_state.user_name, st.session_state.skipped_questions) # Save updated skipped list
            st.toast(f"Question {q_num} removed from skipped list.")

        try:
            # Find the index of the desired question in the current playlist
            index = st.session_state.current_playlist.index(q_num)
            go_to_playlist_index(index)
        except ValueError:
            st.warning(f"Question {q_num} is not in the current playlist. It might be filtered out or not in the current shuffled sequence.")

    except ValueError:
        st.error("Invalid question number. Please enter a whole number.")

def skip_current_question():
    """
    Adds the current question to the skipped list, rebuilds the playlist,
    and saves the updated skipped list for the current user.
    """
    if not st.session_state.current_playlist:
        st.warning("No question to skip.")
        return

    current_q = st.session_state.current_playlist[st.session_state.playlist_index]
    st.session_state.skipped_questions.add(current_q)
    st.toast(f"Question {current_q} skipped!")

    # Rebuild playlist to exclude the just-skipped question
    build_playlist()

    # Adjust playlist index after skipping: try to stay at current index, or move back if at end
    if st.session_state.playlist_index >= len(st.session_state.current_playlist) and len(st.session_state.current_playlist) > 0:
        st.session_state.playlist_index = len(st.session_state.current_playlist) - 1
    elif len(st.session_state.current_playlist) == 0:
        st.session_state.playlist_index = 0 # Reset if playlist becomes empty

    # Save skipped questions immediately after skipping
    if st.session_state.user_name:
        save_skipped_questions(st.session_state.user_name, st.session_state.skipped_questions)

def parse_skipped_input():
    """
    Parses the comma-separated string from the skipped questions text area.
    Updates the `skipped_questions` set, rebuilds the playlist, and saves.
    """
    input_string = st.session_state.skipped_questions_textarea # Get value from session state
    new_skipped = set()
    for num_str in input_string.split(','):
        try:
            num = int(num_str.strip())
            if MIN_QUESTION <= num <= MAX_QUESTION:
                new_skipped.add(num)
        except ValueError:
            continue # Ignore invalid entries
    
    st.session_state.skipped_questions = new_skipped
    build_playlist()
    
    # Save after parsing and updating
    if st.session_state.user_name:
        save_skipped_questions(st.session_state.user_name, st.session_state.skipped_questions)

# --- Streamlit UI Layout ---

# Configure the Streamlit page
st.set_page_config(layout="centered", page_title="DP-900 Flashcards")

st.title("DP-900 Flashcards")

# Initialize all session state variables
initialize_session_state()

# --- Passcode Authentication ---
if not st.session_state.authenticated:
    st.subheader("Enter Passcode to Access App")
    passcode_input = st.text_input("Passcode:", type="password", key="passcode_input")
    if st.button("Submit Passcode"):
        if passcode_input == APP_PASSCODE:
            st.session_state.authenticated = True
            st.rerun() # Rerun the app to show the main content
        else:
            st.error("Incorrect passcode. Please try again.")
    st.stop() # Stop execution if not authenticated

# --- Initial Setup on First Run (after authentication) ---
# This ensures the playlist is built and an image is displayed when the app first loads.
# This block is moved up to ensure playlist is built before any UI elements try to access it.
if not st.session_state.current_playlist:
    build_playlist()


# --- User Name Input and Persistence in Sidebar ---
with st.sidebar:
    st.header("User Settings")
    
    # Text input for user name. Use a key to link it to session_state.
    new_user_name = st.text_input("Enter your name:", value=st.session_state.user_name, key="username_input")
    
    # Logic to handle user name change and load/save data
    if new_user_name != st.session_state.user_name:
        st.session_state.user_name = new_user_name
        if st.session_state.user_name:
            # Load skipped questions for the new user
            st.session_state.skipped_questions = load_skipped_questions(st.session_state.user_name)
            build_playlist() # Rebuild playlist with loaded skipped questions
            st.success(f"Loaded skipped questions for {st.session_state.user_name}.")
        else:
            # Clear skipped questions if no username is provided
            st.session_state.skipped_questions = set() 
            build_playlist()
            st.info("Please enter a name to save your progress.")

    st.markdown("---") # Add a separator
    # --- Skipped Questions List Display and Input in Sidebar ---
    st.subheader("Skipped Questions List")
    # Convert the set of skipped questions to a sorted, comma-separated string for display
    skipped_list_str = ",".join(map(str, sorted(list(st.session_state.skipped_questions))))

    st.text_area(
        "Edit skipped questions (comma-separated numbers):", # Label is now visible in sidebar
        value=skipped_list_str,
        height=100,
        key="skipped_questions_textarea", # Link to session_state
        on_change=parse_skipped_input # Call function when textarea content changes
    )


# --- Main Controls (All on one line and horizontally aligned) ---
# Create a single row of columns for all main controls
# Adjusted column ratios to fit all elements comfortably on one line
# Removed col_q_label as its content will be part of col_q_num's text_input
col_prev, col_q_num, col_next, col_shuffle, col_answer, col_skip = st.columns([0.8, 2.3, 0.8, 1.5, 1.5, 1.5]) 

with col_prev:
    st.button("<<", on_click=lambda: go_to_playlist_index(st.session_state.playlist_index - 1), use_container_width=True)

with col_q_num:
    # Display the current question number in the input box
    current_q_display = ""
    if st.session_state.current_playlist:
        current_q_display = str(st.session_state.current_playlist[st.session_state.playlist_index])
    
    # Text input for direct question number navigation, now using placeholder for '#'
    st.text_input(
        "Question", # Provide a label for semantic purposes, but hide it
        value=current_q_display, 
        key="question_num_input", # Link to session_state
        on_change=go_to_question_by_number, # Call function when input changes
        label_visibility="collapsed", # This hides the label in the UI
        placeholder="#" # Use '#' as a placeholder directly in the input field
    )

with col_next:
    st.button("\>>", on_click=lambda: go_to_playlist_index(st.session_state.playlist_index + 1), use_container_width=True)

with col_shuffle:
    # Toggle shuffle mode
    st.button(
        f"Shuffle: {'On' if st.session_state.is_shuffled else 'Off'}",
        on_click=lambda: setattr(st.session_state, 'is_shuffled', not st.session_state.is_shuffled) or build_playlist(),
        use_container_width=True
    )
with col_answer:
    # Toggle between showing question and answer
    st.button(
        "Question?" if st.session_state.showing_answer else "Answer?",
        on_click=lambda: setattr(st.session_state, 'showing_answer', not st.session_state.showing_answer),
        use_container_width=True
    )
with col_skip:
    # Skip the current question
    st.button("Skip Current", on_click=skip_current_question, use_container_width=True)

st.divider()

# --- Flashcard Image Display ---
# This function is called every time the app reruns to update the image
update_flashcard_image() 

st.divider()