import hashlib
import bcrypt
import StringIO

from sqlalchemy import create_engine, func, select
from sqlalchemy import Table, Column, Integer, String, Unicode, Boolean, DateTime, Float
from sqlalchemy import ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy import func, or_, not_, and_

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


#friendship = Table(
#    'friendship', Base.metadata,
#    Column('friend_a_id', Integer, ForeignKey('user.id'), primary_key=True),
#    Column('friend_b_id', Integer, ForeignKey('user.id'), primary_key=True)
#)
class Friendship(Base):
    __tablename__ = "friendship"
    friend_a_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    friend_b_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    confirmed = Column(Boolean, nullable=False, default=False)

    friend_a = relationship(
        "User", foreign_keys=[friend_a_id],
    )
    friend_b = relationship(
        "User", foreign_keys=[friend_b_id],
    )


class User(Base):
    __tablename__ = "user"

    id       = Column(Integer, primary_key=True)
    username = Column(Unicode, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    email    = Column(Unicode, default=None, nullable=True)

    # this relationship is used for persistence
    friends = relationship("User", secondary=Friendship.__table__,
                           primaryjoin=id==Friendship.friend_a_id,
                           secondaryjoin=id==Friendship.friend_b_id,
    )
    friend_requests_incoming = relationship(
        "Friendship", primaryjoin=and_(id==Friendship.friend_b_id, Friendship.confirmed==False))
    friend_requests_sent = relationship(
        "Friendship", primaryjoin=and_(id==Friendship.friend_a_id, Friendship.confirmed==False))

    def __init__(self, username, password, email=None, password_crypt=None):
        self.username = username
        self.password = bcrypt.hashpw(password, bcrypt.gensalt())
        self.email = email
        if password_crypt:
            self.password = password_crypt

    def check_password(self, password):
        return bcrypt.hashpw(password, self.password) == self.password

    def __repr__(self):
        return "<User('%s')>" % (self.name, )


# this relationship is viewonly and selects across the union of all
# friends
friendship_union = (
    select([Friendship.friend_a_id, Friendship.friend_b_id]).where(Friendship.confirmed==True)
).union(
    select([Friendship.friend_b_id, Friendship.friend_a_id]).where(Friendship.confirmed==True)
).alias()

User.all_friends = relationship('User',
                       secondary=friendship_union,
                       primaryjoin=User.id==friendship_union.c.friend_a_id,
                       secondaryjoin=User.id==friendship_union.c.friend_b_id,
                       viewonly=True)


class Survey(Base):
    __tablename__ = "survey"

    id      = Column(Integer, primary_key=True)
    name    = Column(String, unique=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    description = Column(Unicode, nullable=False)
    long_description = Column(Unicode, nullable=False)

    user = relationship(
        "User",
        backref=backref('surveys')
    )

    def set_questions(self, qs):
        for q in qs:
            self.questions.append(q)
            if q.flip:
                self.questions.append(q.flip)


class Question(Base):
    __tablename__ = "question"

    id        = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey('survey.id'), nullable=False, index=True)
    flip_id   = Column(Integer, ForeignKey('question.id'), nullable=True, index=True)
    order     = Column(Float, nullable=False, default=0)
    text      = Column(Unicode, nullable=False)
    extra     = Column(Unicode, nullable=True)

    survey = relationship(
        "Survey",
        backref=backref('questions', order_by=[order.asc(), id.asc()])
    )
    flip = relationship(
        "Question", remote_side=[id], post_update=True,
    )

    def __init__(self, text, flip_text=None, extra=None):
        self.text = text
        if flip_text:
            self.flip = Question(flip_text)
            self.flip.flip = self
        self.extra = extra

    def matches(self, other):
        if self.flip:
            return self.flip == other
        else:
            return self == other


class Response(Base):
    __tablename__ = "response"

    id       = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    survey_id = Column(Integer, ForeignKey('survey.id'), nullable=False, index=True)
    privacy  = Column(String, nullable=False, default="private")

    user = relationship(
       "User",
        backref=backref('responses', cascade="all")
    )
    survey = relationship(
       "Survey",
        backref=backref('responses', cascade="all")
    )

    def value(self, question_id):
        for a in self.answers:
            if a.question.id == question_id:
                return a.value
        return 0


class Answer(Base):
    __tablename__ = "answer"

    id       = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('question.id'), nullable=False, index=True)
    response_id = Column(Integer, ForeignKey('response.id'), nullable=False, index=True)
    value = Column(Integer, nullable=True)

    question = relationship(
       "Question",
	backref=backref("answers", cascade="all", order_by=[id.asc()])
    )
    response = relationship(
       "Response",
        backref=backref('answers', cascade="all")
    )

    def value_name(self):
        return {
            -2: "do not want",
            -1: "do not want",
            0: "don't care about",
            1: "would try",
            2: "like",
        }[self.value]


class Key(Base):
    __tablename__ = "key"

    id       = Column(Integer, primary_key=True)
    key      = Column(String, unique=True)
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    survey_id = Column(Integer, ForeignKey('survey.id'), nullable=False, index=True)
    viewer_id = Column(Integer, ForeignKey('user.id'), nullable=True, index=True)

    owner = relationship(
       "User", foreign_keys=[owner_id],
    )
    survey = relationship(
       "Survey",
    )
    viewer = relationship(
       "User", foreign_keys=[owner_id],
    )




metadata = Base.metadata

if __name__ == "__main__":
    metadata.create_all(engine)
