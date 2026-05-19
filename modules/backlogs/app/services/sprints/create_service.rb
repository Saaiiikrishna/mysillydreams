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

class Sprints::CreateService < BaseServices::Create
  def instance_class
    Sprint
  end

  protected

  def set_attributes_params(params)
    super.except(:goal, :goal_project)
  end

  def after_perform(service_call)
    super.tap do
      persist_goal(service_call) if service_call.success?
    end
  end

  private

  def persist_goal(service_call)
    goal_text = params[:goal]
    return if goal_text.nil?

    sprint = service_call.result
    return if goal_text.blank?

    sprint_goal = SprintGoal.new(sprint:, project: sprint.project, text: goal_text)
    persist_sprint_goal(service_call, sprint_goal)
  rescue ActiveRecord::RecordNotUnique
    service_call.errors.add(:project_id, :project_already_has_goal)
    service_call.success = false
  end

  def persist_sprint_goal(service_call, sprint_goal)
    return if sprint_goal.save

    service_call.merge!(
      ServiceResult.failure(result: sprint_goal, errors: sprint_goal.errors)
    )
  end
end
