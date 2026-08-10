# Domain Context

## Weather Query

A request to resolve a user-provided text or GPS position to a Taiwan Location and produce a weather response.

## Weather Query Result

The outcome of a Weather Query. It contains the response text and zero to three resolved candidate Locations:

- Zero Locations represent an invalid, unsupported, or unmatched query.
- One Location represents the exact Location used for both the weather response and Query History.
- Two or three Locations represent choices shown to the user through LINE Quick Reply.

The weather module owns Location resolution and creates the Weather Query Result. The LINE event module consumes the result to send a response and coordinate Query History.

## Query History

A record that connects a LINE user to the single Location selected by a successful Weather Query. The user module owns persistence; the LINE event module coordinates recording it.
