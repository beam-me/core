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
