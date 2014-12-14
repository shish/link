import hashlib
import StringIO

from sqlalchemy import create_engine, func
from sqlalchemy import Column, Integer, String, Unicode, Boolean, DateTime
from sqlalchemy import ForeignKey, Table
from sqlalchemy.orm import relationship, backref

import ConfigParser
config = ConfigParser.SafeConfigParser()
config.read("../app/link.cfg")
host = config.get("database", "hostname")
user = config.get("database", "username")
password = config.get("database", "password")
database = config.get("database", "database")
engine = create_engine("postgres://%s:%s@%s/%s" % (user, password, host, database), echo=False)


from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id       = Column(Integer, primary_key=True)
    username = Column(Unicode, nullable=False, index=True)
    password = Column(String(32), nullable=False)
    email    = Column(Unicode, default=u"")

    def __init__(self, username, password, email):
        self.username = username
        self.password = hashlib.md5("replace-with-bcrypt-"+username.lower()+password).hexdigest()
        self.email = email

    def __repr__(self):
        return "<User('%s')>" % (self.name, )


metadata = Base.metadata

if __name__ == "__main__":
    metadata.create_all(engine)
