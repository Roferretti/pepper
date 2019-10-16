"""
The Pepper Responder Package contains logic to determine the correct response to a given Natural Language query.
"""

from .responder import Responder, ResponsePicker, ResponderType
from .conversational import GreetingResponder, GoodbyeResponder, ThanksResponder, AffirmationResponder, \
    NegationResponder
from .personal import QnAResponder
from .sensory import VisionResponder, PreviousUtteranceResponder, LocationResponder, IdentityResponder, TimeResponder
from .internet import WikipediaResponder, WolframResponder
from .brain import BrainResponder
from .intention import MeetIntentionResponder
from .unknown import UnknownResponder
