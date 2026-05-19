# frozen_string_literal: true

#-- copyright
# OpenProject is an open source project management software.
# Copyright (C) the OpenProject GmbH
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License version 3.
#
# OpenProject is a fork of ChiliProject, which is a fork of Redmine. The copyright follows:
# Copyright (C) 2006-2013 Jean-Philippe Lang
# Copyright (C) 2010-2013 the ChiliProject Team
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# See COPYRIGHT and LICENSE files for more details.
#++

module Backlogs
  module Sprints
    class GoalForm < ApplicationForm
      attr_reader :project, :disabled, :show_separator

      def initialize(project:, disabled: false, show_separator: false)
        @project = project
        @disabled = disabled
        @show_separator = show_separator
        super()
      end

      form do |f|
        f.separator if show_separator

        f.text_field(
          name: :goal,
          label: goal_label,
          value: goal_value,
          caption: goal_caption,
          disabled:,
          full_width: true
        )
      end

      def goal_label
        label = attribute_name(:goal)
        label += " #{I18n.t('backlogs.sprint_form.goal_for_this_project_suffix')}" if shared_sprint?
        label
      end

      def goal_value
        model.goal_text_for(project)
      end

      def goal_caption
        I18n.t("backlogs.sprint_form.goal_caption") if shared_sprint?
      end

      private

      def shared_sprint?
        model.persisted? && !model.owned_by?(project)
      end
    end
  end
end
