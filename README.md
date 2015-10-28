1kp API
===

API to setup uplaoding of posts.


###Setup

    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt
    // Start Postgres
    createdb onekp
    python mananage.py setup
    createdb onekptesting

###Running

    python wsgi.py


### Accessing The Server

    ssh -i ~/.ssh/sonder.pem ubuntu@52.4.50.233