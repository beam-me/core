-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- Create a table to store your code artifacts
create table if not exists code_artifacts (
  id uuid primary key default gen_random_uuid(),
  run_id text not null,
  problem_description text not null,
  file_path text not null,
  code_content text,
  metadata jsonb default '{}'::jsonb,
  embedding vector(1536), -- OpenAI text-embedding-3-small dimension
  created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Create a function to search for similar code artifacts
create or replace function match_code_artifacts (
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  run_id text,
  problem_description text,
  file_path text,
  code_content text,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    code_artifacts.id,
    code_artifacts.run_id,
    code_artifacts.problem_description,
    code_artifacts.file_path,
    code_artifacts.code_content,
    1 - (code_artifacts.embedding <=> query_embedding) as similarity
  from code_artifacts
  where 1 - (code_artifacts.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
end;
$$;

-- ABN SYSTEM TABLES --

-- 1. Core Registry
create table if not exists core_registry (
  core_id text primary key,
  public_key_pem text not null,
  created_at timestamp with time zone default timezone('utc'::text, now())
);

-- 2. ABN Channels
create table if not exists abn_channels (
  channel_id text primary key,
  task_id text not null,
  origin_core text not null,
  target_core text not null,
  negotiation_budget int default 10,
  expires_at timestamp with time zone not null,
  revoked boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now())
);

-- 3. ABN Transcripts
create table if not exists abn_transcripts (
  id uuid primary key default gen_random_uuid(),
  trace_id text not null,
  channel_id text not null references abn_channels(channel_id),
  seq int not null,
  origin_core text not null,
  target_core text not null,
  msg_type text not null,
  payload_hash text,
  payload_path text,
  policy_decision jsonb default '{}'::jsonb,
  gateway_verif jsonb default '{}'::jsonb,
  detectors jsonb default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now())
);
