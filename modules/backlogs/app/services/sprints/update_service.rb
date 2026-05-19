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

class Sprints::UpdateService < BaseServices::Update
  def instance_class
    Sprint
  end

  protected

  def set_attributes(params)
    attrs = set_attributes_params(params)
    effective_contract = attrs[:attributes].blank? ? EmptyContract : contract_class

    attributes_service_class
      .new(user:, model: instance(params), contract_class: effective_contract, contract_options:)
      .call(attrs)
  end

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
    project = params[:goal_project] || sprint.project

    return unless user.allowed_in_project?(:create_sprints, project)

    persist_goal_text(service_call, sprint, project, goal_text)
  rescue ActiveRecord::RecordNotUnique
    service_call.errors.add(:project_id, :project_already_has_goal)
    service_call.success = false
  end

  def persist_goal_text(service_call, sprint, project, goal_text)
    sprint_goal = SprintGoal.find_or_initialize_by(sprint:, project:)

    if goal_text.present?
      sprint_goal.text = goal_text
      persist_sprint_goal(service_call, sprint_goal)
    elsif sprint_goal.persisted?
      destroy_sprint_goal(service_call, sprint_goal)
    end
  end

  def persist_sprint_goal(service_call, sprint_goal)
    return if sprint_goal.save

    service_call.merge!(
      ServiceResult.failure(result: sprint_goal, errors: sprint_goal.errors)
    )
  end

  def destroy_sprint_goal(service_call, sprint_goal)
    destroyed_goal = sprint_goal.destroy
    return if destroyed_goal.destroyed?

    service_call.merge!(
      ServiceResult.failure(result: sprint_goal, errors: sprint_goal.errors)
    )
  end
end
