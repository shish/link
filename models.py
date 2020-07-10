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
from sqlalchemy.orm import backref, relationship

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

    user = relationship("User", backref=backref("surveys"))

    def get_contents(self):
        return sorted(list(self.questions) + list(self.headings))

    def set_contents(self, qs):
        for n, q in enumerate(qs):
            if isinstance(q, Question):
                q.order = n
                self.questions.append(q)
                if q.flip:
                    q.flip.order = n + 0.5
                    self.questions.append(q.flip)
            elif isinstance(q, Heading):
                q.order = n
                self.headings.append(q)

    contents = property(get_contents, set_contents)


class Question(Base):
    __tablename__ = "question"
    entry_type = "question"

    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=False, index=True)
    flip_id = Column(Integer, ForeignKey("question.id"), nullable=True, index=True)
    order = Column(Float, nullable=False, default=0)
    text = Column(Unicode, nullable=False)
    extra = Column(Unicode, nullable=True)

    survey = relationship(
        "Survey", backref=backref("questions", order_by=[order.asc(), id.asc()])
    )
    flip = relationship("Question", remote_side=[id], post_update=True, cascade="all")

    def __init__(self, text, flip_text=None, extra=None):
        self.text = text
        if flip_text:
            self.flip = Question(flip_text)
            self.flip.flip = self
        self.extra = extra

    def __repr__(self):
        return "Question(%r, %r)" % (self.order, self.text)

    def __lt__(self, other):
        if not other:
            log.warning("Comparing %r against None" % self)
            return 0

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


class Heading(Base):
    __tablename__ = "heading"
    entry_type = "heading"

    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=False, index=True)
    order = Column(Float, nullable=False, default=0)
    text = Column(Unicode, nullable=False)

    survey = relationship(
        "Survey", backref=backref("headings", order_by=[order.asc(), id.asc()])
    )

    def __init__(self, text):
        self.text = text

    def __lt__(self, other):
        return self.order < other.order

    @property
    def is_first_of_pair(self):
        return False

    @property
    def is_second_of_pair(self):
        return False


class Response(Base):
    __tablename__ = "response"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=False, index=True)
    privacy = Column(String, nullable=False, default="private")

    user = relationship("User", backref=backref("responses", cascade="all"))
    survey = relationship("Survey", backref=backref("responses", cascade="all"))

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

    question = relationship(
        "Question", backref=backref("answers", cascade="all", order_by=[id.asc()])
    )
    response = relationship("Response", backref=backref("answers", cascade="all"))

    def value_name(self):
        return {
            -2: "do not want",
            -1: "do not want",
            0: "don't care about",
            1: "would try",
            2: "like",
        }[self.value]
