# slackbot

create slackbot with some permission like oauth permission
install the slackbot app in our slack
put slackbot credentials in .env file and also get github personal access  token and username for github access
create splunk enterprise edition login also put splunk username and password
install ollama from this website https://ollama.com/       for: linux,mac or windows
run this command on terminal after ollama installation => ollama run phi 
phi is a small language model. which model we use only change the model name and run above command
anaconda environment used for this project
install all required packages after clone this repository
run this command for 1st time after creating conda env => ollama pull phi
and run the slackbot.py using python slackbot.py command
open the slackbot, ask any question to slackbot. slackbot answered by llm's knowledge.
you need ask from your git codebase. just type "github" from slack.
"Received /git message. Initiating git process..." => slackbot return this process. 
and ask some questions from your git codebase after see this message "Please ask a question related to GitHub."
you finish this github session. just type "github exit" quit from this session.
you need ask some query from your splunk. just type "splunk" from slack.
ask query after see this message from slack "You said: splunk.Please ask a question related to Splunk."
example query is => search index=_internal error , search index=_internal warning etc,,,
you quit this session simply type and enter "splunk exit".

.env file

# slack 
SLACK_BOT_TOKEN =
SLACK_APP_TOKEN =

# github
github_token=
github_username =

# splunk
SPLUNK_USERNAME = haja
SPLUNK_PASSWORD = Haja@321









