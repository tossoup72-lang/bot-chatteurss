# Bot de recrutement et de progression des chatteurs

Bot Discord en français et en anglais pour une agence MYM / OnlyFans : il recrute les candidats, teste leurs compétences avec l'IA, propose un niveau, intègre les nouveaux chatteurs, suit leurs performances et te propose des push dans un salon privé.

## Ce que fait le bot

| Étape | Ce qui se passe |
|---|---|
| **Candidature** | Bouton *Postuler* ou `/postuler` → langue → confirmation 18+ → 5 questions (expérience, plateformes, disponibilités, meilleur résultat, motivation). Le bot vérifie l'expérience minimale et la disponibilité, puis prévient les responsables. |
| **Test** | Fil privé de 30 à 40 min : QCM consignes, QCM anglais, 2 questions de vente, 3 objections, puis simulation de 6 échanges avec un abonné fictif joué par l'IA. |
| **Niveau** | L'IA note les réponses écrites et la simulation, le bot calcule un score pondéré, liste points forts et faibles et propose Débutant, Junior ou Confirmé (Expert se gagne sur le terrain). Un responsable valide d'un clic. |
| **Intégration** | Le nouveau chatteur reçoit en MP son parcours : règlement, fiches des modèles, plan de chatting, scripts, planning, rapports. Il coche chaque étape ; relances automatiques s'il n'a pas fini. |
| **Suivi** | Les ventes viennent de rapports CSV importés par un responsable (jamais de chiffres déclarés). `/mon-niveau` affiche la progression vers le niveau suivant, `/objectifs` les objectifs de la semaine. Bilan hebdo en MP chaque lundi, classement et promotions possibles dans le salon admin. |
| **Push** | Dans ton salon privé, `/push` génère des messages de masse humanisés, chauds et taquins (suggestifs, jamais explicites), dans la voix de chaque modèle. Propositions automatiques à 11 h et 20 h 30. |

## Commandes

**Tout le monde** : `/postuler`, `/test`, `/mon-niveau`, `/objectifs`, `/parcours`

**Responsables** (`/admin …`) : `candidats`, `fiche`, `valider`, `refuser`, `autoriser`, `niveau`, `desactiver`, `promotions`, `objectif`, `bilan`, `import`, `modele-csv`, `modele`, `modeles`, `panneau`

**Toi seul, dans le salon des push** : `/push modele type [theme] [nombre]`

Les messages du salon admin ont des boutons : *Valider*, *Choisir le niveau*, *Refuser*, *Autoriser le test*, *Promouvoir*.

## Installation (environ 30 minutes)

### 1. Créer l'application Discord
1. Va sur https://discord.com/developers/applications → *New Application*.
2. Onglet **Bot** : *Reset Token* et copie le token (`DISCORD_TOKEN`). Active **Server Members Intent** et **Message Content Intent**.
3. Onglet **OAuth2 > URL Generator** : coche `bot` et `applications.commands`, puis les permissions *Manage Roles*, *Manage Threads*, *Create Private Threads*, *Send Messages*, *Send Messages in Threads*, *Embed Links*, *Attach Files*, *Read Message History*. Ouvre le lien pour inviter le bot.
4. Dans *Paramètres du serveur > Rôles*, place le rôle du bot **au-dessus** des rôles de niveau, sinon il ne pourra pas les attribuer.

### 2. Préparer le serveur
Active le mode développeur pour pouvoir copier les ID :
- **Sur ordinateur** : clique sur l'engrenage ⚙️ en bas à gauche, à côté de ton pseudo (*Paramètres utilisateur*). Dans la colonne de gauche, section *Paramètres de l'appli*, ouvre **Avancés** et active **Mode développeur**.
- **Sur téléphone** : touche ta photo de profil en bas à droite, puis l'engrenage ⚙️ en haut, descends jusqu'à **Avancés** et active **Mode développeur**.

Ensuite, fais un clic droit (ou un appui long sur téléphone) sur un salon, un rôle, un membre ou le nom du serveur, puis **Copier l'identifiant**. Pour un rôle, passe par *Paramètres du serveur > Rôles* et fais un clic droit sur le rôle.

- **Salons** : `#recrutement` (visible de tous), `#tests` (candidats sans accès, le bot y crée des fils privés), `#admin-recrutement` (responsables seulement), `#push` (**toi et le bot uniquement**), `#bienvenue` (optionnel).
- **Rôles** : Responsable, Candidat, Chatteur, Débutant, Junior, Confirmé, Expert.
- Dans `agency_settings.py`, remplace les `channel_id: 0` du parcours par les ID de tes salons règlement, fiches modèles, plan de chatting, scripts, planning et rapports.

### 3. Base Supabase
1. Dans ton projet Supabase, ouvre *SQL Editor*, colle le contenu de `supabase/schema.sql` et exécute.
2. *Project Settings > API* : copie l'URL (`SUPABASE_URL`) et la clé **service_role** (`SUPABASE_SERVICE_KEY`). Cette clé donne un accès complet : ne la mets que dans Railway.

### 4. Clé IA
Crée une clé sur https://console.anthropic.com (`ANTHROPIC_API_KEY`). Un test complet coûte quelques centimes.

### 5. Hébergement Railway
1. Mets ce dossier sur un dépôt GitHub **privé**.
2. Sur https://railway.com : *New Project > Deploy from GitHub repo*.
3. Onglet *Variables* : colle toutes les variables de `.env.example` remplies.
4. Railway lance `python main.py` automatiquement (voir `railway.json`). Dans les logs, tu dois voir « commandes synchronisées » puis « Connecté en tant que… ».

### 6. Premier lancement
1. Dans `#recrutement`, tape `/admin panneau` pour publier le bouton *Postuler*.
2. Pour chaque modèle, `/admin modele nom:Eva` et remplis sa personnalité, sa façon d'écrire et ses limites : c'est ce qui rend les push crédibles.
3. **Phase de test** : avec un second compte Discord, fais une candidature complète, valide-la, importe un faux CSV (`/admin modele-csv` donne le modèle), puis vérifie `/mon-niveau`. N'importe les vraies données de l'agence qu'ensuite.

## Import des ventes
`/admin modele-csv` envoie le modèle. Une ligne par chatteur et par période (une semaine conseillée) :

```
discord_id;chatteur;periode_debut;periode_fin;ca;messages_envoyes;ventes;conversations;qualite;ponctualite
```

Le séparateur `;` ou `,` et les dates `2026-10-05` ou `05/10/2026` sont acceptés. `qualite` et `ponctualite` sont des notes sur 100 données par un responsable. Le taux de conversion est calculé : ventes ÷ conversations. Réimporter la même période remplace les chiffres.

## Personnaliser
- `agency_settings.py` : commissions par niveau (8 / 10 / 12 / 15 % par défaut), critères d'éligibilité, poids du test, seuils de niveau, conditions de promotion, règles de l'agence, étapes du parcours, horaires des push et des bilans.
- `questions.py` : QCM, questions ouvertes et abonnés fictifs de la simulation.
- `i18n.py` : tous les textes du bot en français et en anglais.

Les chiffres par défaut sont des points de départ : ajuste-les à tes conditions réelles.

## Structure

```
main.py              démarrage, synchronisation des commandes
config.py            variables d'environnement
agency_settings.py   réglages métier
ai.py                notation, abonné fictif, push, conseils (Claude)
db.py                accès Supabase
scoring.py           score, niveau proposé, conditions de promotion
csv_import.py        lecture des rapports de ventes
questions.py         banque de questions
i18n.py              textes FR / EN
services.py          recruter, refuser, changer de niveau
cogs/                recruitment, tests, admin, progression, onboarding, push
supabase/schema.sql  tables de la base
```
