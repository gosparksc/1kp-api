1kp API
===

API to setup uploading of posts.


###Setup

    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt
    // Start Postgres
    createdb onekp
    python3 manage.py setup
    createdb onekptesting

###Running

    source env/bin/activate
    python3 wsgi.py


### Accessing The Server

    ssh -i ~/.ssh/sonder.pem ubuntu@52.4.50.233
