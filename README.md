# 1000 Pitches API (1kp-api)

An API for the 1000 Pitches app, plus an extremely simple web interface for viewing the pitches.

#### About 1000 Pitches

1000 Pitches is an annual "pitch competition" that gets students thinking entrepreneurially. Each fall, USC students have the chance to submit a 30-second video pitch in exchange for a free 1000 Pitches T-Shirt. Most students pitch spontaneously after being accosted while walking around campus, enticed by the idea of free stuff. The competition collects over 1000 ideas each Fall, and awards the top ideas with industry connections, mentorship, and other cool prizes.


### Setup

    virtualenv -p python3 env
    source env/bin/activate
    pip install -r requirements.txt
    // Start Postgres
    createdb onekp
    python3 manage.py setup
    createdb onekptesting

### Running

    source env/bin/activate
    python3 wsgi.py


### Accessing The Server

    ssh -i ~/.ssh/sonder.pem ubuntu@52.4.50.233

### Deploying to AWS

Use the Elastic Beanstalk CLI for deploying to AWS.