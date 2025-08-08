-- Supabase schema: multi-tenant org/project/task app with RLS
-- Run in Supabase SQL editor or via psql. Wraps changes in a transaction.

BEGIN;

-- 1) Extensions & settings
CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions; -- gen_random_uuid(), gen_random_bytes()
CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA extensions;  -- text search indexing support

SET search_path = public, extensions;

-- 2) Types
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'org_role') THEN
    CREATE TYPE org_role AS ENUM ('owner', 'admin', 'member', 'viewer');
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_status') THEN
    CREATE TYPE task_status AS ENUM ('todo', 'in_progress', 'done', 'archived');
  END IF;
END $$;

-- 3) Helper functions
CREATE OR REPLACE FUNCTION public.current_user_id()
RETURNS uuid
LANGUAGE sql STABLE AS $$
  select auth.uid();
$$;

CREATE OR REPLACE FUNCTION public.is_authenticated()
RETURNS boolean
LANGUAGE sql STABLE AS $$
  select auth.uid() is not null;
$$;

-- updated_at trigger helper
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

-- 4) Tables

-- profiles mirror of auth.users
CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text,
  full_name text,
  avatar_url text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS profiles_email_trgm_idx ON public.profiles USING gin (email gin_trgm_ops);

-- organizations
CREATE TABLE IF NOT EXISTS public.organizations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text UNIQUE,
  plan text NOT NULL DEFAULT 'free',
  owner_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT organizations_slug_format CHECK (slug IS NULL OR slug ~ '^[a-z0-9-]+$')
);

-- organization membership
CREATE TABLE IF NOT EXISTS public.organization_members (
  org_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role org_role NOT NULL DEFAULT 'member',
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (org_id, user_id)
);

-- helper functions that depend on organization_members
CREATE OR REPLACE FUNCTION public.is_org_member(target_org_id uuid)
RETURNS boolean
LANGUAGE sql STABLE AS $$
  select exists (
    select 1 from public.organization_members m
    where m.org_id = target_org_id and m.user_id = auth.uid()
  );
$$;

CREATE OR REPLACE FUNCTION public.is_org_admin(target_org_id uuid)
RETURNS boolean
LANGUAGE sql STABLE AS $$
  select exists (
    select 1 from public.organization_members m
    where m.org_id = target_org_id and m.user_id = auth.uid() and m.role in ('owner','admin')
  );
$$;

-- projects
CREATE TABLE IF NOT EXISTS public.projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  created_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT projects_unique_name_per_org UNIQUE (org_id, name)
);

-- tasks
CREATE TABLE IF NOT EXISTS public.tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  title text NOT NULL,
  description text,
  status task_status NOT NULL DEFAULT 'todo',
  assignee_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  priority int,
  due_date date,
  created_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS tasks_project_id_idx ON public.tasks (project_id);
CREATE INDEX IF NOT EXISTS tasks_status_idx ON public.tasks (status);

-- comments
CREATE TABLE IF NOT EXISTS public.comments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid NOT NULL REFERENCES public.tasks(id) ON DELETE CASCADE,
  author_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  body text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS comments_task_id_created_at_idx ON public.comments (task_id, created_at desc);

-- invitations
CREATE TABLE IF NOT EXISTS public.invitations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
  email text NOT NULL,
  role org_role NOT NULL,
  token text NOT NULL UNIQUE DEFAULT encode(gen_random_bytes(16), 'hex'),
  invited_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  accepted boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz
);

-- activity log
CREATE TABLE IF NOT EXISTS public.activity_log (
  id bigserial PRIMARY KEY,
  org_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
  actor_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  action text NOT NULL,
  subject_type text NOT NULL,
  subject_id uuid,
  meta jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS activity_log_org_created_idx ON public.activity_log (org_id, created_at desc);

-- 5) Triggers

-- updated_at triggers
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'set_profiles_updated_at'
  ) THEN
    CREATE TRIGGER set_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'set_organizations_updated_at'
  ) THEN
    CREATE TRIGGER set_organizations_updated_at
    BEFORE UPDATE ON public.organizations
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'set_projects_updated_at'
  ) THEN
    CREATE TRIGGER set_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'set_tasks_updated_at'
  ) THEN
    CREATE TRIGGER set_tasks_updated_at
    BEFORE UPDATE ON public.tasks
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'set_comments_updated_at'
  ) THEN
    CREATE TRIGGER set_comments_updated_at
    BEFORE UPDATE ON public.comments
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
  END IF;
END $$;

-- insert profile on new user signups
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  INSERT INTO public.profiles (id, email)
  VALUES (NEW.id, NEW.email)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'on_auth_user_created'
  ) THEN
    CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
  END IF;
END $$;

-- when organization is created, add owner to members
CREATE OR REPLACE FUNCTION public.handle_org_created()
RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  INSERT INTO public.organization_members(org_id, user_id, role)
  VALUES (NEW.id, NEW.owner_id, 'owner')
  ON CONFLICT DO NOTHING;
  RETURN NEW;
END;
$$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'on_organization_created'
  ) THEN
    CREATE TRIGGER on_organization_created
    AFTER INSERT ON public.organizations
    FOR EACH ROW EXECUTE FUNCTION public.handle_org_created();
  END IF;
END $$;

-- basic activity logging triggers for projects, tasks, comments
CREATE OR REPLACE FUNCTION public.log_activity()
RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
  related_org uuid;
  actor uuid;
  subj_type text;
  subj_id uuid;
  details jsonb;
BEGIN
  actor := coalesce(auth.uid(), NEW.created_by, NEW.author_id);

  IF TG_TABLE_NAME = 'projects' THEN
    related_org := COALESCE(NEW.org_id, OLD.org_id);
    subj_type := 'project';
    subj_id := COALESCE(NEW.id, OLD.id);
  ELSIF TG_TABLE_NAME = 'tasks' THEN
    SELECT p.org_id INTO related_org FROM public.projects p WHERE p.id = COALESCE(NEW.project_id, OLD.project_id);
    subj_type := 'task';
    subj_id := COALESCE(NEW.id, OLD.id);
  ELSIF TG_TABLE_NAME = 'comments' THEN
    SELECT p.org_id INTO related_org FROM public.tasks t JOIN public.projects p ON p.id = t.project_id WHERE t.id = COALESCE(NEW.task_id, OLD.task_id);
    subj_type := 'comment';
    subj_id := COALESCE(NEW.id, OLD.id);
  ELSE
    related_org := null; subj_type := TG_TABLE_NAME; subj_id := null;
  END IF;

  details := jsonb_build_object(
    'op', TG_OP,
    'table', TG_TABLE_NAME,
    'new', to_jsonb(NEW),
    'old', to_jsonb(OLD)
  );

  IF related_org IS NOT NULL THEN
    INSERT INTO public.activity_log(org_id, actor_id, action, subject_type, subject_id, meta)
    VALUES (
      related_org,
      actor,
      TG_OP,
      subj_type,
      subj_id,
      details
    );
  END IF;

  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  END IF;
  RETURN NEW;
END;
$$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'log_projects_activity'
  ) THEN
    CREATE TRIGGER log_projects_activity
    AFTER INSERT OR UPDATE OR DELETE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION public.log_activity();
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'log_tasks_activity'
  ) THEN
    CREATE TRIGGER log_tasks_activity
    AFTER INSERT OR UPDATE OR DELETE ON public.tasks
    FOR EACH ROW EXECUTE FUNCTION public.log_activity();
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'log_comments_activity'
  ) THEN
    CREATE TRIGGER log_comments_activity
    AFTER INSERT OR UPDATE OR DELETE ON public.comments
    FOR EACH ROW EXECUTE FUNCTION public.log_activity();
  END IF;
END $$;

-- 6) RLS & policies
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_log ENABLE ROW LEVEL SECURITY;

-- profiles policies
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='profiles' AND policyname='Profiles are viewable by self'
  ) THEN
    CREATE POLICY "Profiles are viewable by self" ON public.profiles
      FOR SELECT USING (id = auth.uid());
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='profiles' AND policyname='Users can update own profile'
  ) THEN
    CREATE POLICY "Users can update own profile" ON public.profiles
      FOR UPDATE USING (id = auth.uid()) WITH CHECK (id = auth.uid());
  END IF;
END $$;

-- organizations policies
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Org members can select orgs'
  ) THEN
    CREATE POLICY "Org members can select orgs" ON public.organizations
      FOR SELECT USING (public.is_org_member(id));
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Users can create orgs they own'
  ) THEN
    CREATE POLICY "Users can create orgs they own" ON public.organizations
      FOR INSERT WITH CHECK (owner_id = auth.uid());
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Org admins can update orgs'
  ) THEN
    CREATE POLICY "Org admins can update orgs" ON public.organizations
      FOR UPDATE USING (public.is_org_admin(id));
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Org owner can delete org'
  ) THEN
    CREATE POLICY "Org owner can delete org" ON public.organizations
      FOR DELETE USING (EXISTS (
        SELECT 1 FROM public.organization_members m
        WHERE m.org_id = organizations.id AND m.user_id = auth.uid() AND m.role = 'owner'
      ));
  END IF;
END $$;

-- organization_members policies
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Members can view membership rows of their orgs'
  ) THEN
    CREATE POLICY "Members can view membership rows of their orgs" ON public.organization_members
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.organization_members me
          WHERE me.org_id = organization_members.org_id AND me.user_id = auth.uid()
        )
      );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Admins can manage membership in their orgs'
  ) THEN
    CREATE POLICY "Admins can manage membership in their orgs" ON public.organization_members
      FOR ALL USING (public.is_org_admin(org_id)) WITH CHECK (public.is_org_admin(org_id));
  END IF;
END $$;

-- projects policies
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Org members can select projects'
  ) THEN
    CREATE POLICY "Org members can select projects" ON public.projects
      FOR SELECT USING (public.is_org_member(org_id));
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Members can insert projects in their org'
  ) THEN
    CREATE POLICY "Members can insert projects in their org" ON public.projects
      FOR INSERT WITH CHECK (public.is_org_member(org_id) AND created_by = auth.uid());
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Members can update projects in their org'
  ) THEN
    CREATE POLICY "Members can update projects in their org" ON public.projects
      FOR UPDATE USING (public.is_org_member(org_id));
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Admins can delete projects'
  ) THEN
    CREATE POLICY "Admins can delete projects" ON public.projects
      FOR DELETE USING (public.is_org_admin(org_id));
  END IF;
END $$;

-- tasks policies (join to project/org inside EXISTS)
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Members can select tasks'
  ) THEN
    CREATE POLICY "Members can select tasks" ON public.tasks
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.projects p
          JOIN public.organization_members m ON m.org_id = p.org_id AND m.user_id = auth.uid()
          WHERE p.id = tasks.project_id
        )
      );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Members can insert tasks'
  ) THEN
    CREATE POLICY "Members can insert tasks" ON public.tasks
      FOR INSERT WITH CHECK (
        EXISTS (
          SELECT 1 FROM public.projects p
          JOIN public.organization_members m ON m.org_id = p.org_id AND m.user_id = auth.uid()
          WHERE p.id = tasks.project_id
        ) AND created_by = auth.uid()
      );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Members can update tasks'
  ) THEN
    CREATE POLICY "Members can update tasks" ON public.tasks
      FOR UPDATE USING (
        EXISTS (
          SELECT 1 FROM public.projects p
          JOIN public.organization_members m ON m.org_id = p.org_id AND m.user_id = auth.uid()
          WHERE p.id = tasks.project_id
        )
      );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Admins can delete tasks'
  ) THEN
    CREATE POLICY "Admins can delete tasks" ON public.tasks
      FOR DELETE USING (
        EXISTS (
          SELECT 1 FROM public.projects p
          JOIN public.organization_members m ON m.org_id = p.org_id AND m.user_id = auth.uid() AND m.role in ('owner','admin')
          WHERE p.id = tasks.project_id
        )
      );
  END IF;
END $$;

-- comments policies
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Members can select comments'
  ) THEN
    CREATE POLICY "Members can select comments" ON public.comments
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.tasks t
          JOIN public.projects p ON p.id = t.project_id
          JOIN public.organization_members m ON m.org_id = p.org_id AND m.user_id = auth.uid()
          WHERE t.id = comments.task_id
        )
      );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Members can insert comments'
  ) THEN
    CREATE POLICY "Members can insert comments" ON public.comments
      FOR INSERT WITH CHECK (
        EXISTS (
          SELECT 1 FROM public.tasks t
          JOIN public.projects p ON p.id = t.project_id
          JOIN public.organization_members m ON m.org_id = p.org_id AND m.user_id = auth.uid()
          WHERE t.id = comments.task_id
        ) AND author_id = auth.uid()
      );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Authors or admins can update comments'
  ) THEN
    CREATE POLICY "Authors or admins can update comments" ON public.comments
      FOR UPDATE USING (
        author_id = auth.uid() OR EXISTS (
          SELECT 1 FROM public.tasks t
          JOIN public.projects p ON p.id = t.project_id
          JOIN public.organization_members m ON m.org_id = p.org_id AND m.user_id = auth.uid() AND m.role in ('owner','admin')
          WHERE t.id = comments.task_id
        )
      );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Authors or admins can delete comments'
  ) THEN
    CREATE POLICY "Authors or admins can delete comments" ON public.comments
      FOR DELETE USING (
        author_id = auth.uid() OR EXISTS (
          SELECT 1 FROM public.tasks t
          JOIN public.projects p ON p.id = t.project_id
          JOIN public.organization_members m ON m.org_id = p.org_id AND m.user_id = auth.uid() AND m.role in ('owner','admin')
          WHERE t.id = comments.task_id
        )
      );
  END IF;
END $$;

-- invitations policies (admins only)
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Admins can manage invitations'
  ) THEN
    CREATE POLICY "Admins can manage invitations" ON public.invitations
      FOR ALL USING (public.is_org_admin(org_id)) WITH CHECK (public.is_org_admin(org_id));
  END IF;
END $$;

-- activity_log policies (readable by org members; insert via trigger only)
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname='Members can select activity logs'
  ) THEN
    CREATE POLICY "Members can select activity logs" ON public.activity_log
      FOR SELECT USING (public.is_org_member(org_id));
  END IF;
END $$;

-- 7) Views (optional)
CREATE OR REPLACE VIEW public.my_memberships AS
SELECT m.org_id, o.name as org_name, m.role, m.created_at
FROM public.organization_members m
JOIN public.organizations o ON o.id = m.org_id
WHERE m.user_id = auth.uid();

-- 8) Storage: bucket and RLS on storage.objects for org-bound uploads
-- Create a private bucket for app uploads
INSERT INTO storage.buckets (id, name, public)
VALUES ('app-uploads', 'app-uploads', false)
ON CONFLICT (id) DO NOTHING;

-- Storage policies on storage.objects for bucket 'app-uploads'
-- Convention: put org id in metadata->>'org_id' as a uuid string

ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='storage' AND tablename='objects' AND policyname='Org members can read objects in app-uploads'
  ) THEN
    CREATE POLICY "Org members can read objects in app-uploads" ON storage.objects
      FOR SELECT USING (
        bucket_id = 'app-uploads'
        AND metadata ? 'org_id'
        AND EXISTS (
          SELECT 1 FROM public.organization_members m
          WHERE m.user_id = auth.uid() AND m.org_id = (metadata->>'org_id')::uuid
        )
      );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='storage' AND tablename='objects' AND policyname='Org members can insert into app-uploads'
  ) THEN
    CREATE POLICY "Org members can insert into app-uploads" ON storage.objects
      FOR INSERT WITH CHECK (
        bucket_id = 'app-uploads'
        AND auth.uid() IS NOT NULL
        AND metadata ? 'org_id'
        AND EXISTS (
          SELECT 1 FROM public.organization_members m
          WHERE m.user_id = auth.uid() AND m.org_id = (metadata->>'org_id')::uuid
        )
      );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='storage' AND tablename='objects' AND policyname='Owner or admins can update/delete objects'
  ) THEN
    CREATE POLICY "Owner or admins can update/delete objects" ON storage.objects
      FOR UPDATE USING (
        bucket_id = 'app-uploads' AND (
          owner = auth.uid() OR EXISTS (
            SELECT 1 FROM public.organization_members m
            WHERE m.user_id = auth.uid() AND m.org_id = (metadata->>'org_id')::uuid AND m.role in ('owner','admin')
          )
        )
      ) WITH CHECK (
        bucket_id = 'app-uploads' AND (
          owner = auth.uid() OR EXISTS (
            SELECT 1 FROM public.organization_members m
            WHERE m.user_id = auth.uid() AND m.org_id = (metadata->>'org_id')::uuid AND m.role in ('owner','admin')
          )
        )
      );
  END IF;
END $$;

-- 9) Useful grants (Supabase uses postgres role auth users; no extra grants needed for RLS)
-- Intentionally left minimal; adjust if you have custom roles

COMMIT;

-- Optional seeds (commented out). Uncomment to create a sample org and project for the current user.
-- BEGIN;
-- INSERT INTO public.organizations (name, slug, owner_id) VALUES ('Demo Org', 'demo-org', auth.uid());
-- INSERT INTO public.projects (org_id, name, description, created_by)
-- SELECT o.id, 'Welcome Project', 'First project', auth.uid() FROM public.organizations o WHERE o.slug = 'demo-org';
-- COMMIT;