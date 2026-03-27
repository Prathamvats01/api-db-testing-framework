-- ─────────────────────────────────────────────────────────────────
-- init.sql — Auto-runs when the PostgreSQL container starts.
-- Creates 4 tables mirroring JSONPlaceholder entities and seeds them
-- with realistic data so DB tests run immediately out of the box.
-- ─────────────────────────────────────────────────────────────────

-- ── Users ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    username   VARCHAR(50)  NOT NULL UNIQUE,
    email      VARCHAR(150) NOT NULL UNIQUE,
    phone      VARCHAR(30),
    website    VARCHAR(100),
    created_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ── Posts ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS posts (
    id      SERIAL PRIMARY KEY,
    user_id INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title   VARCHAR(255) NOT NULL,
    body    TEXT         NOT NULL
);

-- ── Comments ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS comments (
    id      SERIAL PRIMARY KEY,
    post_id INTEGER      NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    name    VARCHAR(255) NOT NULL,
    email   VARCHAR(150) NOT NULL,
    body    TEXT         NOT NULL
);

-- ── Todos ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS todos (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(255) NOT NULL,
    completed   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- Seed Data
-- ─────────────────────────────────────────────────────────────────

INSERT INTO users (name, username, email, phone, website) VALUES
    ('Leanne Graham',         'Bret',             'Sincere@april.biz',          '1-770-736-8031', 'hildegard.org'),
    ('Ervin Howell',          'Antonette',         'Shanna@melissa.tv',          '010-692-6593',   'anastasia.net'),
    ('Clementine Bauch',      'Samantha',          'Nathan@yesenia.net',         '1-463-123-4447', 'ramiro.info'),
    ('Patricia Lebsack',      'Karianne',          'Julianne.OConner@kory.org',  '493-170-9623',   'kale.biz'),
    ('Chelsey Dietrich',      'Kamren',            'Lucio_Hettinger@annie.ca',   '(254)954-1289',  'demarco.info'),
    ('Mrs. Dennis Schulist',  'Leopoldo_Corkery',  'Karley_Dach@jasper.info',    '1-477-935-8478', 'ola.org'),
    ('Kurtis Weissnat',       'Elwyn.Skiles',      'Telly.Hoeger@billy.biz',     '210.067.6132',   'elvis.io'),
    ('Nicholas Runolfsdottir','Maxime_Nienow',     'Sherwood@rosamond.me',       '586.493.6943',   'jacynthe.com'),
    ('Glenna Reichert',       'Delphine',          'Chaim_McDermott@dana.io',    '(775)976-6794',  'conrad.com'),
    ('Clementina DuBuque',    'Moriah.Stanton',    'Rey.Padberg@karina.biz',     '024-648-3804',   'ambrose.net');

INSERT INTO posts (user_id, title, body) VALUES
    (1, 'sunt aut facere repellat provident',   'quia et suscipit suscipit recusandae consequuntur'),
    (1, 'qui est esse',                         'est rerum tempore vitae sequi sint nihil'),
    (1, 'ea molestias quasi exercitationem',    'et iusto sed quo iure voluptatem'),
    (2, 'eum et est occaecati',                 'ullam et saepe reiciendis voluptatem adipisci'),
    (2, 'nesciunt quas odio',                   'repudiandae veniam quaerat sunt sed alias aut'),
    (3, 'dolorem eum magni eos aperiam quia',   'ut aspernatur corporis harum nihil quis provident'),
    (4, 'magnam facilis autem',                 'dolore placeat quibusdam ea quo vitae'),
    (5, 'dolorem dolore est ipsam',             'dignissimos aperiam dolorem qui eum facilis quibusdam'),
    (6, 'nesciunt iure omnis dolorem tempora',  'consectetur animi nesciunt iure dolore enim quia ad'),
    (7, 'optio molestias id quia eum',          'quo et expedita modi cum officia vel magni'),
    (8, 'distinctio vitae autem aut',           'suscipit nam nisi quo aperiam aut asperiores'),
    (9, 'asperiores commodi amet',              'non et omnis qui aspernatur aut saepe ullam'),
    (10,'provident id voluptas',                'harum sequi sint nihil reprehenderit dolor beatae');

INSERT INTO comments (post_id, name, email, body) VALUES
    (1, 'id labore ex et quam laborum',  'Eliseo@gardner.biz',       'laudantium enim quasi est quidem magnam voluptate'),
    (1, 'quo vero reiciendis velit',     'Jayne@junit.us',           'est natus enim nihil est dolore omnis voluptatem'),
    (2, 'odio adipisci rerum aut animi', 'Nikita@garfield.biz',      'quia molestiae reprehenderit quasi aspernatur'),
    (2, 'alias odio sit',                'Lew@alysha.tv',            'non et atque occaecati deserunt quas accusantium'),
    (3, 'vero eaque aliquid doloribus',  'Hayden@althea.biz',        'harum non quasi et ratione tempore iure'),
    (4, 'et fugit eligendi deleniti',    'Presley@jacob.biz',        'doloribus at sed quis culpa deserunt'),
    (5, 'repellat consequatur praesentium', 'Mallory@cheap.biz',     'totam corporis dignissimos'),
    (6, 'est minima sapiente',           'Oswald@brennan.org',       'nihil vitae est ullam dolorem et'),
    (7, 'harum aliquid ratione',         'Adriana.Zboncak@jeanette.me','eligendi et voluptatem sunt'),
    (8, 'consequatur placeat omnis',     'Genevieve@telly.io',       'adipisci numquam et omnis dolorem'),
    (9, 'natus corrupti maxime',         'Korbin@francesca.com',     'aut voluptatem repellat fugit vitae'),
    (10,'provident id voluptas',         'Kenton.Runolfsson@elvis.tv','consequuntur deleniti eos quia'),
    (11,'et iusto sed quo iure',         'Lola@cali.info',           'reprehenderit aliquam qui voluptate'),
    (12,'quia molestiae reprehenderit',  'Bertrand@rosamond.biz',    'omnis quaerat aut illo temporibus'),
    (13,'sunt aut facere repellat',      'Camille@christian.info',   'voluptatem eligendi minima eveniet');

INSERT INTO todos (user_id, title, completed) VALUES
    (1, 'delectus aut autem',                    FALSE),
    (1, 'quis ut nam facilis et officia qui',     FALSE),
    (1, 'fugiat veniam minus',                   FALSE),
    (1, 'et porro tempora',                      TRUE),
    (1, 'laboriosam mollitia et enim quasi',     FALSE),
    (2, 'qui ullam ratione quibusdam',           FALSE),
    (2, 'illo expedita consequatur quia in',     FALSE),
    (3, 'quo adipisci enim quam ut ab',          TRUE),
    (3, 'molestiae perspiciatis ipsa',           FALSE),
    (4, 'illo est ratione doloremque quia',      TRUE),
    (5, 'vero rerum temporibus dolor',           TRUE),
    (6, 'in delectus aut autem',                 FALSE),
    (7, 'porro iste ipsum rerum',               FALSE),
    (8, 'dolores debitis consequuntur libero',   TRUE),
    (9, 'ut velit iure condimentum vitae',       FALSE),
    (10,'adipisci non ad dicta qui amet',        TRUE);

-- ─────────────────────────────────────────────────────────────────
-- Indexes for query performance
-- ─────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_posts_user_id    ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_todos_user_id    ON todos(user_id);
CREATE INDEX IF NOT EXISTS idx_todos_completed  ON todos(completed);
