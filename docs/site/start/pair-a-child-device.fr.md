# Associer l’appareil d’un enfant

Le profil enfant et l’appareil enfant sont deux éléments distincts. Le profil
contient le nom, le code PIN, les règles et l’historique. L’association autorise
un navigateur, téléphone, tablette ou PWA installée précis à afficher les
profils et à accepter le code PIN d’un enfant.

## Associer l’appareil utilisé actuellement

1. Connectez-vous comme parent sur l’appareil que l’enfant utilisera.
2. Ouvrez **Parents → Réglages → Appareils enfants**.
3. Saisissez un **nom d’appareil** clair, par exemple « Tablette de la cuisine ».
4. Sélectionnez **Autoriser sur cet appareil**.
5. Déconnectez-vous ou ouvrez la page de connexion enfant. L’enfant peut sélectionner son profil et saisir son code PIN à quatre chiffres.

## Associer un autre appareil avec un lien privé

1. Sur un appareil parent connecté, ouvrez **Parents → Réglages → Appareils enfants**.
2. Sélectionnez **Envoyer un lien**.
3. Transmettez le lien de façon privée à l’appareil prévu et ouvrez-le sur celui-ci. Ne le publiez pas dans une discussion de groupe ou une note partagée.
4. Le lien associe l’appareil une seule fois, puis expire après **10 minutes**.

Après l’association, KinKudos affiche une confirmation telle que **Cet appareil
est associé comme Mac · Chrome**. Sans nom personnalisé, la confirmation et la
liste utilisent un résumé général attribué automatiquement.

<img class="screenshot-image" src="../../assets/device-pairing-success-26-6-4.png" alt="Message de réussite de l’association d’un appareil enfant" loading="lazy">

La capture d’écran contient uniquement des données de démonstration fictives.

## Gérer les appareils associés

La liste indique une icône générale, un nom personnalisé facultatif, un résumé
tel que **iPhone · Safari** ou **Tablette Android · Chrome**, un identifiant
stable de six caractères et la dernière utilisation. La classification couvre
les téléphones, tablettes, ordinateurs et appareils inconnus; elle ne promet pas
le modèle exact. Après 30 jours sans utilisation, **Jamais utilisé récemment**
est également affiché.

Renommez les entrées pour les reconnaître. Sur mobile, **Révoquer** est affiché
avec une icône compacte de corbeille. Révoquez immédiatement un appareil perdu,
vendu ou prêté pour une longue durée. La révocation retire l’accès enfant et les
notifications sur cet appareil, sans supprimer le profil ni son historique.

Un appareil associé utilisé activement renouvelle son cookie d’accès afin qu’une
association active n’expire pas silencieusement. La révocation invalide l’accès
immédiatement; l’appareil doit être associé de nouveau.

Après avoir saisi son mot de passe, l’administrateur parent peut choisir
**Révoquer tous les appareils enfants**. Chaque navigateur ou PWA enfant devra
alors être associé de nouveau.

[Retour aux 15 premières minutes →](first-15-minutes.fr.md)
