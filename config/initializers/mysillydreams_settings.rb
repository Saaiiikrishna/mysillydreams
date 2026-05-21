# frozen_string_literal: true

# ── Part 1: runs at initializer load time, BEFORE Settings::Definition.add_all ──
#
# Capture the env-var value BEFORE deleting it. This is critical: if the env
# var was the only authoritative source for the email address (DB row absent or
# defaulted to openproject@example.net), we must persist it to the DB or mail
# delivery will break after we clear the env var.
#
# We clear the env var so that Settings::Definition.add_all (called in
# after_initialize) never marks mail_from as writable=false, which would lock
# the UI field and make Setting.mail_from= raise NotWritableError.
MSD_ENV_MAIL_FROM = %w[OPENPROJECT_MAIL__FROM OPENPROJECT_MAIL_FROM]
                    .map { |k| ENV.delete(k) }
                    .compact
                    .first

# ── Part 2: runs after Rails + DB are fully loaded ───────────────────────────
#
# Ensures the DB always has a valid mail_from value and applies the display
# name rename (MySillyDreams → Octaleads). Idempotent after first run.
Rails.application.config.after_initialize do
  has_table = begin
    ActiveRecord::Base.connection.table_exists?(:settings)
  rescue StandardError
    false
  end
  next unless has_table

  row     = ActiveRecord::Base.connection
                              .select_one("SELECT value FROM settings WHERE name = 'mail_from'")
  db_val  = row&.fetch("value", nil).to_s

  # If the DB has no row or only has the upstream default, seed it from the
  # env var we captured above so the real address is not lost.
  base = if db_val.present? && db_val != "openproject@example.net"
           db_val
         elsif MSD_ENV_MAIL_FROM.present?
           MSD_ENV_MAIL_FROM
         else
           db_val
         end

  # Apply display name rename
  target = base.gsub("MySillyDreams Notifications", "Octaleads Notifications")

  if target == db_val
    # Already correct — nothing to do
  elsif row
    Setting.where(name: "mail_from").update_all(value: target)
    Setting.clear_cache
    Rails.logger.info "[MSD] mail_from updated → #{target}"
  else
    conn = ActiveRecord::Base.connection
    conn.execute(
      "INSERT INTO settings (name, value, updated_at) VALUES " \
      "('mail_from', #{conn.quote(target)}, NOW())"
    )
    Setting.clear_cache
    Rails.logger.info "[MSD] mail_from inserted → #{target}"
  end
rescue StandardError => e
  Rails.logger.warn "[MSD] mail_from update failed: #{e.message}"
end
