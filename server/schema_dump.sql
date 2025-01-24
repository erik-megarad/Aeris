CREATE TABLE api_keys (
    id integer NOT NULL DEFAULT nextval('api_keys_id_seq'::regclass),
    uuid uuid DEFAULT gen_random_uuid(),
    user_id integer NOT NULL,
    project_id integer NOT NULL,
    key text NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone,
    active boolean DEFAULT true
    PRIMARY KEY (id)
    FOREIGN KEY (user_id) REFERENCES users(id)
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE events (
    id integer NOT NULL DEFAULT nextval('events_id_seq'::regclass),
    uuid uuid DEFAULT gen_random_uuid(),
    task_id integer NOT NULL,
    event_type text NOT NULL,
    event_data jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now()
    PRIMARY KEY (id)
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE project (
    id integer NOT NULL DEFAULT nextval('project_id_seq'::regclass),
    uuid uuid DEFAULT gen_random_uuid(),
    name text NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now()
    PRIMARY KEY (id)
);

CREATE TABLE projects (
    id integer NOT NULL DEFAULT nextval('projects_id_seq'::regclass),
    uuid uuid DEFAULT gen_random_uuid(),
    name text NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now()
    PRIMARY KEY (id)
);

CREATE TABLE task_embeddings (
    id integer NOT NULL DEFAULT nextval('task_embeddings_id_seq'::regclass),
    uuid uuid DEFAULT gen_random_uuid(),
    task_id integer NOT NULL,
    embedding USER-DEFINED NOT NULL
    PRIMARY KEY (id)
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE task_metadata (
    id integer NOT NULL DEFAULT nextval('task_metadata_id_seq'::regclass),
    uuid uuid DEFAULT gen_random_uuid(),
    task_id integer NOT NULL,
    key text NOT NULL,
    value jsonb NOT NULL
    PRIMARY KEY (id)
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE task_tools (
    task_id integer NOT NULL,
    tool_id integer NOT NULL
    PRIMARY KEY (task_id, tool_id)
    FOREIGN KEY (task_id) REFERENCES tasks(id)
    FOREIGN KEY (tool_id) REFERENCES tools(id)
);

CREATE TABLE tasks (
    id integer NOT NULL DEFAULT nextval('tasks_id_seq'::regclass),
    uuid uuid DEFAULT gen_random_uuid(),
    project_id integer NOT NULL,
    name text NOT NULL,
    input text NOT NULL,
    result text,
    success boolean,
    state text NOT NULL DEFAULT 'PENDING'::text,
    created_at timestamp with time zone DEFAULT now()
    PRIMARY KEY (id)
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE tools (
    id integer NOT NULL DEFAULT nextval('tools_id_seq'::regclass),
    uuid uuid DEFAULT gen_random_uuid(),
    name text NOT NULL,
    description text,
    parameters jsonb,
    created_at timestamp with time zone DEFAULT now()
    PRIMARY KEY (id)
);

CREATE TABLE user_projects (
    user_id integer NOT NULL,
    project_id integer NOT NULL
    PRIMARY KEY (project_id, user_id)
    FOREIGN KEY (user_id) REFERENCES users(id)
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE users (
    id integer NOT NULL DEFAULT nextval('users_id_seq'::regclass),
    uuid uuid DEFAULT gen_random_uuid(),
    username text NOT NULL,
    email text,
    github_id text,
    created_at timestamp with time zone DEFAULT now()
    PRIMARY KEY (id)
);
