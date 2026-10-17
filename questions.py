"""Banque de questions des tests (français et anglais).

QCM : la première option de chaque liste est la bonne réponse ; le bot
mélange l'ordre à l'affichage. Ajoute ou modifie librement les questions.
"""

RULES_QCM = {
    "fr": [
        ("Un abonné insiste pour rencontrer la modèle en vrai. Que fais-tu ?", [
            "Je refuse avec tact et je recentre la conversation sur le contenu",
            "J'accepte un faux rendez-vous pour déclencher un achat",
            "Je donne la ville de la modèle pour le rassurer",
            "Je le bloque sans rien dire",
        ]),
        ("Un abonné laisse entendre qu'il a 16 ans.", [
            "J'arrête la conversation et je préviens un responsable immédiatement",
            "Je continue normalement, ce n'est pas mon problème",
            "Je lui demande une preuve d'âge et je continue en attendant",
            "Je change de sujet et je continue de vendre",
        ]),
        ("Un abonné propose de payer par PayPal pour avoir une réduction.", [
            "Je refuse : tous les paiements passent par la plateforme",
            "J'accepte si le montant est élevé",
            "Je lui donne le PayPal d'un collègue",
            "J'accepte une seule fois",
        ]),
        ("Un abonné demande -50 % sur un PPV prévu à 30 € dans le plan.", [
            "J'applique uniquement les remises autorisées par le plan de chatting",
            "J'accepte tout de suite pour ne pas perdre la vente",
            "Je baisse à 5 € pour être sûr qu'il achète",
            "Je lui envoie le contenu gratuitement",
        ]),
        ("Ton shift se termine dans 5 minutes.", [
            "Je remplis mes notes abonnés et mon rapport pour le chatteur suivant",
            "Je pars, le suivant se débrouillera",
            "J'envoie un dernier push à tout le monde sans vérifier le plan",
            "Je supprime les conversations en cours",
        ]),
        ("Un abonné demande le vrai prénom et l'Instagram personnel de la modèle.", [
            "Je ne divulgue jamais d'informations personnelles réelles",
            "Je donne le prénom mais pas l'Instagram",
            "Je donne tout s'il achète un gros PPV",
            "Je lui demande d'attendre et je cherche l'info",
        ]),
    ],
    "en": [
        ("A fan keeps asking to meet the model in real life. What do you do?", [
            "Decline tactfully and steer the conversation back to the content",
            "Agree to a fake date to trigger a purchase",
            "Share the model's city to reassure him",
            "Block him without a word",
        ]),
        ("A fan hints that he is 16 years old.", [
            "Stop the conversation and alert a manager immediately",
            "Keep going, it's not my problem",
            "Ask for proof of age and keep chatting meanwhile",
            "Change the subject and keep selling",
        ]),
        ("A fan offers to pay via PayPal to get a discount.", [
            "Refuse: every payment goes through the platform",
            "Accept if the amount is high",
            "Give him a colleague's PayPal",
            "Accept just this once",
        ]),
        ("A fan wants 50% off a PPV priced at 30 in the plan.", [
            "Only apply the discounts allowed by the chatting plan",
            "Accept right away so the sale isn't lost",
            "Drop to 5 to be sure he buys",
            "Send the content for free",
        ]),
        ("Your shift ends in 5 minutes.", [
            "Fill in my fan notes and report for the next chatter",
            "Leave, the next one will figure it out",
            "Send one last mass message without checking the plan",
            "Delete the ongoing conversations",
        ]),
        ("A fan asks for the model's real first name and personal Instagram.", [
            "Never disclose real personal information",
            "Give the first name but not the Instagram",
            "Give everything if he buys a big PPV",
            "Ask him to wait and look up the info",
        ]),
    ],
}

ENGLISH_QCM = [
    ("What does \"I'm down\" usually mean in a chat?", [
        "I'm in / I agree to do it", "I feel sad", "I'm going offline", "I'm lying down",
    ]),
    ("Choose the correct sentence.", [
        "I've been waiting for you all day", "I been waiting you all day",
        "I'm waiting for you since all day", "I have wait for you all day",
    ]),
    ("A fan writes \"don't leave me on read\". He means:", [
        "Don't read my message without answering", "Don't read my messages aloud",
        "Don't leave the conversation", "Don't send me something to read",
    ]),
    ("Which reply sounds the most natural and playful to \"you're such a tease 😏\"?", [
        "maybe… but you like it, don't you? 😌", "I am not a tease. Thank you for your message.",
        "Yes. Do you want to buy content?", "What is a tease?",
    ]),
    ("Pick the correct one: \"___ going to love what I made today\"", [
        "You're", "Your", "You", "Yours",
    ]),
]

SALES_QUESTIONS = {
    "fr": [
        "Un abonné vient de s'abonner et écrit seulement « hey ». Écris tes 2 ou 3 premiers messages "
        "pour créer le lien et préparer une future vente.",
        "Un abonné a déjà acheté un PPV la semaine dernière. Présente-lui un nouveau contenu payant à 25 € "
        "(photos en lingerie rouge, prises ce matin). Écris le message tel que tu l'enverrais.",
    ],
    "en": [
        "A fan just subscribed and only wrote \"hey\". Write your first 2 or 3 messages to build a "
        "connection and set up a future sale.",
        "A fan bought a PPV last week. Pitch a new paid content at 25 (red lingerie photos taken this "
        "morning). Write the message exactly as you would send it.",
    ],
}

OBJECTION_QUESTIONS = {
    "fr": [
        "L'abonné répond : « c'est trop cher pour moi ». Que lui réponds-tu ?",
        "L'abonné dit : « envoie-moi un aperçu gratuit d'abord, après je verrai ». Ta réponse ?",
        "L'abonné écrit : « je repasserai plus tard » alors qu'il semblait intéressé. Ta réponse ?",
    ],
    "en": [
        "The fan replies: \"that's too expensive for me\". What do you answer?",
        "The fan says: \"send me a free preview first, then I'll see\". Your answer?",
        "The fan writes: \"I'll come back later\" even though he seemed interested. Your answer?",
    ],
}

# Abonnés fictifs pour la simulation
SCENARIOS = {
    "fr": [
        {"name": "Marc", "brief": "34 ans, nouvel abonné, timide, budget moyen. Il hésite à acheter et pose "
                                  "beaucoup de questions. À un moment, il demande s'il peut rencontrer la modèle."},
        {"name": "Kevin", "brief": "abonné depuis 3 mois, a acheté 2 PPV. Radin : il négocie tous les prix et "
                                   "réclame du gratuit. Il achète si on le valorise sans céder sur le prix."},
        {"name": "Julien", "brief": "abonné inactif depuis 1 mois, un peu vexé qu'on ne lui ait pas répondu la "
                                    "dernière fois. Il peut redevenir un bon client s'il se sent important."},
    ],
    "en": [
        {"name": "James", "brief": "41, big spender but demanding. He wants to feel special and exclusive. "
                                   "At some point he asks to pay via PayPal to save fees."},
        {"name": "Tyler", "brief": "new subscriber, chatty and flirty, but keeps saying he is broke and "
                                   "asks for free stuff. He buys if the offer feels personal."},
        {"name": "Ryan", "brief": "inactive for a month, a bit annoyed he was ignored last time. He can "
                                  "become a good client again if he feels important."},
    ],
}
