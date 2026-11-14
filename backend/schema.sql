CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('technician', 'supplier', 'customer', 'admin')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS devices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  manufacturer TEXT NOT NULL,
  model TEXT NOT NULL,
  family TEXT,
  ram_types TEXT[] NOT NULL DEFAULT '{}',
  max_ram_gb INT,
  storage_interfaces TEXT[] NOT NULL DEFAULT '{}',
  notes TEXT,
  UNIQUE(manufacturer, model)
);

CREATE TABLE IF NOT EXISTS components (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  component_type TEXT NOT NULL CHECK (component_type IN ('RAM', 'SSD', 'Battery', 'Display', 'Keyboard', 'Other')),
  brand TEXT,
  model TEXT,
  specs JSONB NOT NULL DEFAULT '{}',
  condition TEXT NOT NULL DEFAULT 'Tested',
  price_cents INT NOT NULL DEFAULT 0,
  quantity INT NOT NULL DEFAULT 1,
  location TEXT,
  seller_id UUID REFERENCES users(id),
  status TEXT NOT NULL DEFAULT 'available',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS repair_outcomes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  component_id UUID REFERENCES components(id),
  device_id UUID REFERENCES devices(id),
  technician_id UUID REFERENCES users(id),
  outcome TEXT NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_events (
  id BIGSERIAL PRIMARY KEY,
  event_type TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  actor_id TEXT,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
