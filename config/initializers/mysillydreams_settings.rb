# frozen_string_literal: true

# Ensures the notification sender display name is "Octaleads Notifications"
# regardless of what was previously stored in the settings table.
Rails.application.config.after_initialize do
  Rails.application.reloader.to_prepare do
    current = Setting.mail_from rescue nil
    next unless current&.include?("MySillyDreams Notifications")

    Setting.mail_from = current.gsub("MySillyDreams Notifications", "Octaleads Notifications")
  rescue StandardError => e
    Rails.logger.warn "[MSD] Could not update mail_from setting: #{e.message}"
  end
end
