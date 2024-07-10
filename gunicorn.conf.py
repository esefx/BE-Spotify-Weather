# gunicorn.conf.py

# The socket to bind. A string of the form: 'HOST', 'HOST:PORT', 'unix:PATH'. An IP is a valid HOST.
bind = '0.0.0.0:8000'  # Change as needed

# The number of worker processes for handling requests.
workers = 3  # Adjust as per your machine's capability

# The number of seconds to wait for requests on a Keep-Alive connection.
keepalive = 2

# The maximum number of pending connections.
backlog = 2048

# The timeout in seconds before a worker is killed and a new one is spawned.
timeout = 120  # Adjust based on your application's needs

# The path to a log file to write to.
accesslog = '-'

# The path to a log file to write errors to.
errorlog = '-'

# The granularity of Error log outputs.
loglevel = 'debug'