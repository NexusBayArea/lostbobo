ALTER TABLE discovery_leaderboard ADD COLUMN IF NOT EXISTS tier TEXT;

UPDATE discovery_leaderboard l
SET tier = c.verification_tier
FROM certificates c
WHERE l.certificate_id = c.certificate_id
  AND l.tier IS NULL;

UPDATE discovery_leaderboard SET tier = 'NONE' WHERE tier IS NULL;
