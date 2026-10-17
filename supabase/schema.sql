-- Schéma de la base du bot de recrutement et de progression des chatteurs.
-- À exécuter une fois dans Supabase > SQL Editor.
-- Le bot utilise la clé service_role ; la RLS est activée sans politique
-- publique, donc la clé publishable/anon ne peut rien lire.

create table if not exists candidates (
  discord_id        bigint primary key,
  username          text not null,
  lang              text not null default 'fr' check (lang in ('fr', 'en')),
  experience_months int,
  platforms         text,
  hours_per_week    int,
  availability      text,
  best_result       text,
  motivation        text,
  eligible          boolean,
  eligibility_notes text,
  status            text not null default 'applied'
                    check (status in ('applied', 'ineligible', 'allowed', 'testing', 'tested', 'accepted', 'rejected')),
  test_attempts     int not null default 0,
  decision_by       bigint,
  decision_reason   text,
  applied_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

create table if not exists test_results (
  id                   bigserial primary key,
  discord_id           bigint not null references candidates (discord_id) on delete cascade,
  total_score          numeric(5, 1) not null,
  suggested_level      text,
  sections             jsonb not null,
  transcript           jsonb,
  avg_response_seconds numeric(8, 1),
  created_at           timestamptz not null default now()
);
create index if not exists test_results_member_idx on test_results (discord_id, created_at desc);

create table if not exists chatters (
  discord_id    bigint primary key,
  username      text not null,
  lang          text not null default 'fr' check (lang in ('fr', 'en')),
  level         text not null check (level in ('debutant', 'junior', 'confirme', 'expert')),
  recruit_score numeric(5, 1),
  level_since   timestamptz not null default now(),
  hired_at      timestamptz not null default now(),
  active        boolean not null default true,
  notes         text
);

create table if not exists level_history (
  id         bigserial primary key,
  discord_id bigint not null references chatters (discord_id) on delete cascade,
  old_level  text,
  new_level  text not null,
  changed_by bigint,
  reason     text,
  created_at timestamptz not null default now()
);

create table if not exists performance (
  id                bigserial primary key,
  discord_id        bigint not null references chatters (discord_id) on delete cascade,
  period_start      date not null,
  period_end        date not null,
  revenue           numeric(12, 2) not null default 0,
  messages_sent     int not null default 0,
  sales             int not null default 0,
  conversations     int not null default 0,
  conversion_rate   numeric(6, 2),
  quality_score     numeric(5, 1),
  punctuality_score numeric(5, 1),
  source            text,
  imported_by       bigint,
  created_at        timestamptz not null default now(),
  unique (discord_id, period_start, period_end)
);
create index if not exists performance_member_idx on performance (discord_id, period_end desc);

create table if not exists objectives (
  id         bigserial primary key,
  discord_id bigint,            -- null = objectif pour toute l'équipe
  week_start date not null,
  text       text not null,
  created_by bigint,
  created_at timestamptz not null default now()
);
create index if not exists objectives_week_idx on objectives (week_start);

create table if not exists onboarding_progress (
  discord_id bigint not null,
  step_key   text not null,
  done_at    timestamptz not null default now(),
  primary key (discord_id, step_key)
);

create table if not exists model_profiles (
  id         bigserial primary key,
  name       text not null unique,
  lang       text not null default 'fr' check (lang in ('fr', 'en')),
  persona    text not null,
  style      text,
  limits     text,
  active     boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists push_suggestions (
  id         bigserial primary key,
  model_name text not null,
  push_type  text not null,
  theme      text,
  content    text not null,
  status     text not null default 'proposed' check (status in ('proposed', 'used', 'rejected')),
  created_at timestamptz not null default now()
);

alter table candidates          enable row level security;
alter table test_results        enable row level security;
alter table chatters            enable row level security;
alter table level_history       enable row level security;
alter table performance         enable row level security;
alter table objectives          enable row level security;
alter table onboarding_progress enable row level security;
alter table model_profiles      enable row level security;
alter table push_suggestions    enable row level security;
