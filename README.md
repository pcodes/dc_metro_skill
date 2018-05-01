# DC Metro Times Alexa Skill
Ever wondered when the next train will be arriving in the DC Metro? Using the WMATA train API and Python, this Amazon Alexa skill responds to requests questions about train times from a specific station, as well as questions about the metro system status in general. 

**Note**: This skill is currently unpublished, with an actual release date TBD.

## Features
- Train times from specific stations: Ask for a specific station, and it will respond with all available train times from that station. 
- Metro Status: Is the metro on fire? This skill can tell you
- Fuzzy Matching: Thanks to the [fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy) string-matching library, support for partial station-correctness is available. Example, saying "Foggy" as a station name will auto match to "Foggy Bottom"


