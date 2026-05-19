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

require "spec_helper"

RSpec.describe Sprints::UpdateService, type: :model do
  let(:project) { create(:project) }
  let(:source_project) { create(:project) }
  let(:sprint) { create(:sprint, project: source_project, name: "Sprint 1") }
  let(:user) do
    create(:user, member_with_permissions: { project => project_permissions, source_project => source_project_permissions })
  end
  let(:project_permissions) { %i[view_sprints create_sprints] }
  let(:source_project_permissions) { %i[view_sprints] }
  let(:attributes) { {} }
  let(:goal) { "Ship dashboard" }
  let(:goal_project) { project }

  subject(:service_call) do
    described_class.new(user:, model: sprint).call(attributes:, goal:, goal_project:)
  end

  it "persists the goal for the supplied goal project" do
    expect { service_call }.to change(SprintGoal, :count).by(1)

    expect(service_call.result.goal_text_for(project)).to eq("Ship dashboard")
  end

  context "when a goal already exists" do
    before do
      create(:sprint_goal, sprint:, project:, text: "Old goal")
    end

    it "updates the existing goal" do
      expect { service_call }.not_to change(SprintGoal, :count)

      expect(sprint.goal_text_for(project)).to eq("Ship dashboard")
    end

    context "with a blank goal" do
      let(:goal) { "" }

      it "removes the existing goal" do
        expect { service_call }.to change(SprintGoal, :count).by(-1)

        expect(sprint.goal_text_for(project)).to be_nil
      end
    end
  end

  context "without create_sprints permission in the goal project" do
    let(:project_permissions) { %i[view_sprints] }

    it "does not persist the goal" do
      expect { service_call }.not_to change(SprintGoal, :count)
    end
  end

  context "when goal persistence hits the unique index" do
    before do
      allow(SprintGoal)
        .to receive(:find_or_initialize_by)
        .and_raise(ActiveRecord::RecordNotUnique)
    end

    it "returns a failed service result instead of raising" do
      expect { service_call }.not_to raise_error

      expect(service_call).not_to be_success
      expect(service_call.errors.symbols_for(:project_id)).to include(:project_already_has_goal)
    end
  end

  context "with sprint attributes" do
    let(:attributes) { { name: "Renamed" } }
    let(:goal) { nil }
    let(:project_permissions) { %i[view_sprints] }
    let(:source_project_permissions) { %i[view_sprints create_sprints] }
    let(:goal_project) { source_project }

    it "updates the sprint through the regular update contract" do
      expect(service_call).to be_success

      expect(sprint.reload.name).to eq("Renamed")
    end
  end
end
