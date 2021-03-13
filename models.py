import hashlib
import logging

import bcrypt
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Unicode,
    and_,
    func,
    select,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

log = logging.getLogger(__name__)


Base = declarative_base()


class Sessions(Base):
    __tablename__ = "sessions"
    session_id = Column(String(128), nullable=False, primary_key=True)
    atime = Column(DateTime, nullable=False, default=func.now())
    data = Column(String)


class Friendship(Base):
    __tablename__ = "friendship"
    friend_a_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    friend_b_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    confirmed = Column(Boolean, nullable=False, default=False)

    friend_a = relationship("User", foreign_keys=[friend_a_id])
    friend_b = relationship("User", foreign_keys=[friend_b_id])

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(Unicode, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    email = Column(Unicode, default=None, nullable=True)

    # this relationship is used for persistence
    friends = relationship(
        "User",
        secondary=Friendship.__table__,
        primaryjoin=id == Friendship.friend_a_id,
        secondaryjoin=id == Friendship.friend_b_id,
    )
    friend_requests_incoming = relationship(
        "Friendship",
        primaryjoin=and_(id == Friendship.friend_b_id, Friendship.confirmed == False),
    )
    friend_requests_sent = relationship(
        "Friendship",
        primaryjoin=and_(id == Friendship.friend_a_id, Friendship.confirmed == False),
    )
    surveys = relationship("Survey", back_populates="user")
    responses = relationship("Response", back_populates="user", cascade="all")

    def __init__(self, username, password, email=None, password_crypt=None):
        self.username = username
        self.email = email
        self.set_password(password)
        if password_crypt:
            self.password = password_crypt

    def set_password(self, password):
        given = password.encode()
        self.password = bcrypt.hashpw(given, bcrypt.gensalt()).decode()

    def check_password(self, password):
        given = password.encode()
        current = self.password.encode()
        return bcrypt.hashpw(given, current) == current

    @property
    def token(self):
        return hashlib.md5(self.password.encode()).hexdigest()


# this relationship is viewonly and selects across the union of all friends
friendship_union = (
    (
        select([Friendship.friend_a_id, Friendship.friend_b_id]).where(
            Friendship.confirmed == True
        )
    )
    .union(
        select([Friendship.friend_b_id, Friendship.friend_a_id]).where(
            Friendship.confirmed == True
        )
    )
    .alias()
)

User.all_friends = relationship(
    "User",
    secondary=friendship_union,
    primaryjoin=User.id == friendship_union.c.friend_a_id,
    secondaryjoin=User.id == friendship_union.c.friend_b_id,
    viewonly=True,
)


class Survey(Base):
    __tablename__ = "survey"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    description = Column(Unicode, nullable=False)
    long_description = Column(Unicode, nullable=False)

    user = relationship("User", back_populates="surveys")
    questions = relationship("Question", back_populates="survey")
    responses = relationship("Response", back_populates="survey", cascade="all")

    @property
    def sections(self):
        return {q.section for q in self.questions}

    def get_contents(self):
        return sorted(list(self.questions))

    def set_contents(self, qs):
        for n, q in enumerate(qs):
            q.order = n
            self.questions.append(q)
            if q.flip:
                q.flip.order = n + 0.5
                self.questions.append(q.flip)

    contents = property(get_contents, set_contents)


class Question(Base):
    __tablename__ = "question"
    entry_type = "question"

    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=False, index=True)
    flip_id = Column(Integer, ForeignKey("question.id"), nullable=True, index=True)
    order = Column(Float, nullable=False, default=0)
    section = Column(Unicode, nullable=False)
    text = Column(Unicode, nullable=False)
    extra = Column(Unicode, nullable=True)

    survey = relationship("Survey", back_populates="questions")
    flip = relationship("Question", remote_side=[id], post_update=True, cascade="all")
    answers = relationship("Answer", back_populates="question", cascade="all")

    def __init__(self, section, text, flip_text=None, extra=None):
        self.section = section
        self.text = text
        if flip_text:
            self.flip = Question(section, flip_text)
            self.flip.flip = self
        self.extra = extra

    def __repr__(self):
        return "Question(%r, %r)" % (self.order, self.text)

    def __lt__(self, other):
        if not other:
            log.warning("Comparing %r against None" % self)
            return 0

        if self.section != other.section:
            return self.section < other.section

        if self.flip and other.id == self.flip.id:
            # if comparing with our pair, lower ID comes first
            return self.id < other.id
        else:
            # if comparing to an unrelated object, compare by our pair's main ID
            sort_order = self.order
            if self.flip and self.flip.id < self.id:
                sort_order = self.flip.order
            return sort_order < other.order

    @property
    def is_first_of_pair(self):
        return self.flip and self.id < self.flip.id

    @property
    def is_second_of_pair(self):
        return self.flip and self.id > self.flip.id

    def matches(self, other):
        if self.flip:
            return self.flip.id == other.id
        else:
            return self.id == other.id


class Response(Base):
    __tablename__ = "response"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=False, index=True)
    privacy = Column(String, nullable=False, default="private")

    user = relationship("User", back_populates="responses")
    survey = relationship("Survey", back_populates="responses")
    answers = relationship("Answer", back_populates="response", cascade="all")

    def value(self, question_id):
        for a in self.answers:
            if a.question.id == question_id:
                return a.value
        return 0


class Answer(Base):
    __tablename__ = "answer"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("question.id"), nullable=False, index=True)
    response_id = Column(Integer, ForeignKey("response.id"), nullable=False, index=True)
    value = Column(Integer, nullable=True)

    question = relationship("Question", back_populates="answers")
    response = relationship("Response", back_populates="answers")

    def value_name(self):
        return {
            -2: "do not want",
            -1: "do not want",
            0: "don't care about",
            1: "would try",
            2: "like",
        }[self.value]
