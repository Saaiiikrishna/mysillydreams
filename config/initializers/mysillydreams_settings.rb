# frozen_string_literal: true

# ── Part 1: runs at initializer load time, BEFORE Settings::Definition.add_all ──
#
# OpenProject calls Settings::Definition.add_all in config.after_initialize.
# add_all calls override_value_from_env for every setting; when it finds
# OPENPROJECT_MAIL__FROM in ENV it calls definition.override_value which sets
# writable = false — locking the field in the UI and raising NotWritableError
# on any Setting.mail_from= call.
#
# Clearing the env var here (outside any block) runs before after_initialize,
# so add_all never sees the override, mail_from stays writable, and the
# Administration → Email settings field is fully editable by the super admin.
%w[OPENPROJECT_MAIL__FROM OPENPROJECT_MAIL_FROM].each { |k| ENV.delete(k) }

# ── Part 2: runs after Rails + DB are fully loaded ───────────────────────────
#
# Update the stale display name in the settings table once, preserving whatever
# email address is already configured. Uses update_all (raw SQL path) so it
# works even if the setting was previously marked non-writable in the DB row.
Rails.application.config.after_initialize do
  has_table = begin
    ActiveRecord::Base.connection.table_exists?(:settings)
  rescue StandardError
    false
  end
  next unless has_table

  row = ActiveRecord::Base.connection
                          .select_one("SELECT value FROM settings WHERE name = 'mail_from'")
  current = row&.fetch("value", nil).to_s
  next unless current.include?("MySillyDreams Notifications")

  updated = current.gsub("MySillyDreams Notifications", "Octaleads Notifications")
  Setting.where(name: "mail_from").update_all(value: updated)
  Setting.clear_cache
  Rails.logger.info "[MSD] mail_from updated → #{updated}"
rescue StandardError => e
  Rails.logger.warn "[MSD] mail_from update failed: #{e.message}"
end
