from graphiti_core.nodes import EpisodeType

USSR = [
    {
        'content': 'The Soviet Union was officially established on December 30, 1922, through the Treaty on the Creation of the USSR. Vladimir Lenin was the first leader of the Soviet Union.',
        'type': EpisodeType.text,
        'description': 'Wikipedia article: "Soviet Union"',
    },
    {
        'content': {
            'name': 'Vladimir Lenin',
            'position': 'First Leader of Soviet Union',
            'birth_year': 1870,
            'death_year': 1924,
            'party': 'Bolshevik',
            'key_role': 'Led October Revolution'
        },
        'type': EpisodeType.json,
        'description': 'Britannica Encyclopedia structured data',
    },
    {
        'content': 'After Lenin\'s death in 1924, a power struggle emerged. Joseph Stalin gradually consolidated power and became the dominant leader by the late 1920s, outmaneuvering rivals like Leon Trotsky.',
        'type': EpisodeType.text,
        'description': 'BBC History documentary transcript',
    },
    {
        'content': {
            'name': 'Joseph Stalin',
            'position': 'General Secretary',
            'leadership_period': '1924-1953',
            'birth_year': 1878,
            'death_year': 1953,
            'birthplace': 'Georgia',
            'preceded_by': 'Vladimir Lenin'
        },
        'type': EpisodeType.json,
        'description': 'Academic database: Biography.com profile',
    },
    {
        'content': 'Stalin implemented rapid industrialization through Five-Year Plans starting in 1928. The first Five-Year Plan focused on heavy industry and resulted in massive construction projects like the Magnitogorsk steel plant.',
        'type': EpisodeType.text,
        'description': 'The Guardian newspaper article on Soviet industrialization',
    },
    {
        'content': {
            'policy_name': 'Collectivization',
            'period': '1929-1932',
            'leader': 'Joseph Stalin',
            'target': 'Agricultural system',
            'method': 'Forced consolidation of farms',
            'resistance': 'Kulak opposition',
            'consequence': 'Ukrainian famine (Holodomor)'
        },
        'type': EpisodeType.json,
        'description': 'Harvard University Press research data',
    },
    {
        'content': 'The Great Purge occurred from 1936 to 1938 under Stalin\'s rule. Millions of Soviet citizens were arrested, executed, or sent to gulags. Many high-ranking Communist Party officials and military officers were eliminated.',
        'type': EpisodeType.text,
        'description': 'Podcast transcript: "Hardcore History" by Dan Carlin',
    },
    {
        'content': {
            'event_name': 'World War II',
            'soviet_name': 'Great Patriotic War',
            'period': '1941-1945',
            'initial_aggressor': 'Nazi Germany',
            'key_battles': ['Battle of Stalingrad', 'Siege of Leningrad', 'Battle of Kursk'],
            'soviet_leader': 'Joseph Stalin',
            'outcome': 'Soviet victory'
        },
        'type': EpisodeType.json,
        'description': 'National Geographic historical database',
    },
    {
        'content': 'After Stalin\'s death in 1953, Nikita Khrushchev emerged as the new leader. In 1956, Khrushchev delivered the Secret Speech denouncing Stalin\'s cult of personality and many of his policies.',
        'type': EpisodeType.text,
        'description': 'New York Times historical archives',
    },
    {
        'content': {
            'name': 'Nikita Khrushchev',
            'position': 'First Secretary',
            'leadership_period': '1953-1964',
            'birth_year': 1894,
            'death_year': 1971,
            'key_policy': 'De-Stalinization',
            'preceded_by': 'Joseph Stalin',
            'succeeded_by': 'Leonid Brezhnev'
        },
        'type': EpisodeType.json,
        'description': 'Smithsonian Institute biographical records',
    },
    {
        'content': 'The Cold War intensified under Khrushchev. Key events included the Cuban Missile Crisis in 1962, where the Soviet Union and United States came close to nuclear war. The crisis was resolved when the USSR agreed to remove missiles from Cuba.',
        'type': EpisodeType.text,
        'description': 'CNN documentary script: "Cold War Declassified"',
    },
    {
        'content': {
            'leader_name': 'Leonid Brezhnev',
            'position': 'General Secretary',
            'leadership_period': '1964-1982',
            'era_name': 'Era of Stagnation',
            'key_policy': 'Brezhnev Doctrine',
            'major_event': 'Soviet-Afghan War',
            'preceded_by': 'Nikita Khrushchev'
        },
        'type': EpisodeType.json,
        'description': 'Reuters news agency historical data feed',
    },
    {
        'content': 'Mikhail Gorbachev became General Secretary in 1985 and introduced major reforms: Glasnost (openness) and Perestroika (restructuring). These policies aimed to modernize the Soviet system but ultimately led to its dissolution.',
        'type': EpisodeType.text,
        'description': 'Washington Post interview transcript',
    },
    {
        'content': {
            'name': 'Mikhail Gorbachev',
            'position': 'General Secretary',
            'leadership_period': '1985-1991',
            'birth_year': 1931,
            'death_year': 2022,
            'key_reforms': ['Glasnost', 'Perestroika'],
            'achievement': 'Nobel Peace Prize 1990',
            'role_in_dissolution': 'Last leader of USSR'
        },
        'type': EpisodeType.json,
        'description': 'Associated Press obituary structured data',
    },
    {
        'content': 'The Soviet Union officially dissolved on December 26, 1991. Fifteen independent republics were formed, with Russia being the largest successor state. Boris Yeltsin became the first president of the Russian Federation.',
        'type': EpisodeType.text,
        'description': 'TIME Magazine historical article',
    },
]
