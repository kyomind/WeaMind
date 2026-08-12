# Domain Language

- **Weather Query**: One complete request that resolves a Location, reads fresh forecast data, and attempts Query History as a secondary side effect.
- **Location resolution**: Converting text, an address, or coordinates into a persisted Taiwan Location. When a shared location provides both a valid address and coordinates, the address takes precedence; coordinates are the fallback. Preset queries bypass this step.
- **Query History**: A record that a known user queried a resolved Location. It is recorded even when no fresh weather exists; failure must not fail the Weather Query.
- **Preset Location**: A user's configured home or office Location ID, used directly without name resolution.
