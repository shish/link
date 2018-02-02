#!/usr/bin/env python
from sqlalchemy.orm import scoped_session, sessionmaker
from models import *
import random

metadata.drop_all(engine)
metadata.create_all(engine)

orm = scoped_session(sessionmaker(bind=engine))

alice = User(u"alice", "alicepass")
orm.add(alice)

bob = User(u"bob", "bobpass")
orm.add(bob)

kink = Survey(name="kink", description=u"Test questions: fetish compatibility")
orm.add(kink)

kink.set_questions([
Question(u"Kissing"),
Question(u"Massage (Giving)", u"Massage (Receiving)"),
Question(u"Vanilla Sex"),
Question(u"Experimental positions"),
Question(u"69"),
Question(u"Photography (Taking photos)", u"Photography (Posing)"),
Question(u"Use of mirrors"),
Question(u"Rape fantasy (Raping)", u"Rape fantasy (Being raped)"),
Question(u"Reluctance", u"Being reluctant"),
Question(u"Indifference (Being into it)", u"Indifference (Doing something else)", extra=u"Sex with one person being into it, while the other reads a book, or phones a friend, or otherwise is not giving a fuck (except for literally)"),
Question(u"Enthusiasm", u"Being enthusiastic"),
Question(u"Worshipping", u"Being worshipped"),
Question(u"Threesome"),
Question(u"Outside the bedroom (kitchen / shower / etc)"),
Question(u"Outdoors (woods / etc)"),
Question(u"In a different building (office / church / etc)"),
Question(u"Orgy"),
Question(u"Feet"),
Question(u"Toys (Using)", u"Toys (Receiving)", extra=u"Dildo, vibrator, cock-ring, fleshlight, etc"),
Question(u"Use of sex furniture"),
Question(u"Strap-on (Wearing)", u"Strap-on (Receiving)"),
Question(u"Fellatio (Giving)", u"Fellatio (Receiving)"),
Question(u"Cunnilingus (Giving)", u"Cunnilingus (Receiving)"),
Question(u"Deepthroating"),
Question(u"Spanking", u"Being Spanked"),
Question(u"Dirty talk (Speaking)", u"Dirty talk (Listening)"),
Question(u"Having a pet", u"Being a pet", extra=u"Not necessarily animal related, more behaviour; curling up in a lap, stroking, rewarding with treats, etc"),
Question(u"Being a master / mistress", u"Being a slave"),
Question(u"Giving a collar", u"Wearing a collar"),
Question(u"Costume Play"),
Question(u"Role Play"),
Question(u"Furry"),
Question(u"Handjob (Giving)", u"Handjob (Receiving)"),
Question(u"Orgasm Control", u"Having orgasm controlled"),
Question(u"Pain in general (Giving)", u"Pain in general (Receiving)"),
Question(u"Choking", u"Being Choked"),
Question(u"Hairpulling", u"Having hair pulled"),
Question(u"Biting", u"Being bitten"),
Question(u"Whipping", u"Being Whipped"),
Question(u"Hot wax (Dripping)", u"Hot wax (Being dripped on)"),
Question(u"Latex/Rubber"),
Question(u"Leather"),
Question(u"Bondage (Tying)", u"Bondage (Being tied)"),
Question(u"Ropeplay"),
Question(u"Blindfolding", u"Being blindfolded"),
Question(u"Gagging", u"Being gagged"),
Question(u"Sounding", u"Being sounded"),
Question(u"Oviposition (Laying)", u"Oviposition (Inserting / Watching)", extra=u"Egg-laying"),
Question(u"Waking them up sexually", u"Being woken up sexually", extra=u"Morning blow-job, etc"),
Question(u"Watch porn together"),
Question(u"Nipple play", u"Having nipples played with"),
Question(u"Milking", u"Being milked"),
Question(u"Facial Ejaculation (Giving)", u"Facial ejeculation (Receiving)"),
Question(u"Paizuri (Giving)", u"Paizuri (Receiving)", extra=u"Tit-fucking"),
Question(u"Bukkake (Giving)", u"Bukkake (Receiving)", extra=u"Creating a semen waterfall~"),
Question(u"Anal sex (Giving)", u"Anal sex (Receiving)"),
Question(u"Anal fingering (Giving)", u"Anal fingering (Receiving)"),
Question(u"Anal fisting", u"Being anally fisted"),
Question(u"Rimming (Giving)", u"Rimming (Receiving)"),
Question(u"Vaginal fisting", u"Being vaginally fisted"),
Question(u"Felching"),
Question(u"Watersports"),
Question(u"Scat"),
Question(u"Vore"),
Question(u"Gore"),
Question(u"NTR fantasy"),
Question(u"Visiting kink clubs"),
Question(u"Visiting kink trade shows", extra=u"(Think MCM Expo, without children)"),
])

r = Response(survey=kink, user=alice)
for q in kink.questions:
    Answer(response=r, question=q, value=random.choice([-2, -1, 0, 1, 2]))
orm.add(r)

r = Response(survey=kink, user=bob)
for q in kink.questions:
    Answer(response=r, question=q, value=random.choice([-2, -1, 0, 1, 2]))
orm.add(r)

orm.commit()
