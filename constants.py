# Contest Status Messages
START_SUCCESS = "{typist_role} The typing contest has started! Please join the contest using `!join`."
END_SUCCESS = "{typist_role} The typing contest has ended!"
STATUS_ACTIVE = "A typing contest is currently active!"
STATUS_INACTIVE = "No active contest at the moment."
CONTEST_ALREADY_ACTIVE = "The typing contest is already active!"
NO_ACTIVE_CONTEST = "No typing contest is currently active."

# User Participation Messages
JOIN_SUCCESS = "{user} has joined the typing contest!"
QUIT_SUCCESS = "{user} has quit the typing contest!"
ALREADY_JOINED = "You are already in the contest."
NOT_IN_CONTEST = "You are not in the contest."
NOT_CONTEST_CREATOR = (
    "You are not authorized to use this command. Only the contest creator can."
)
NO_PARTICIPANTS = "No participants have joined the contest yet."
MEMBER_NOT_IN_GUILD = (
    "{member} is no longer in the server or is not a valid member."
)
MEMBER_NOT_IN_CONTEST = "{member} is not in the contest."
REMOVE_SUCCESS = "{member} has been removed from the contest."
BAN_SUCCESS = "{user} has been banned from the contest."
BANNED_USER_TRY_JOIN = "{user}, you are banned from joining the contest."

# Round and WPM Messages
INVALID_WPM = "Please provide a valid positive integer for WPM."
ROUND_NOT_STARTED = "No round has been started yet."
REMINDER_SUCCESS = "The following participants haven't submitted their WPM yet:\n{pending_participants}\nPlease submit your WPM using `!wpm {{wpm}}`"
ALL_SUBMITTED_SUCCESS = (
    "All participants have submitted their WPM for this round."
)
MUST_SUBMIT_WPM = "At least one participant must submit a WPM before advancing to the next round."

# Ranking and Emojis
RANKING_EMOJIS = [":first_place:", ":second_place:", ":third_place:"]
CHECKMARK_EMOJI = "\u2705"  # \u2705 is equivalent to :white_check_mark: emoji

# Idle threshold minutes
IDLE_THRESHOLD_MINUTES = 10

# Roles
PARTICIPANT_ROLE_NAME = "Participant"

# File Paths
CONFIG_JSON_FILE_PATH = "./config/config.json"
