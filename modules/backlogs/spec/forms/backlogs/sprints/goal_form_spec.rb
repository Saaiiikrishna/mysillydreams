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

require "rails_helper"

RSpec.describe Backlogs::Sprints::GoalForm, type: :forms do
  include ViewComponent::TestHelpers

  let(:project) { create(:project) }
  let(:sprint) { create(:sprint, project:) }
  let(:disabled) { false }
  let(:show_separator) { false }
  let(:form_arguments) { { url: "/foo", model: sprint, scope: :sprint } }

  def render_form
    render_in_view_context(
      described_class,
      form_arguments,
      project,
      disabled,
      show_separator
    ) do |described_class, form_arguments, project, disabled, show_separator|
      primer_form_with(**form_arguments) do |f|
        render(described_class.new(f, project:, disabled:, show_separator:))
      end
    end
  end

  subject(:rendered_form) do
    render_form
    page
  end

  it "renders the goal field" do
    expect(rendered_form).to have_field(Sprint.human_attribute_name(:goal), disabled: false)
  end

  context "when a goal exists for the project" do
    before do
      create(:sprint_goal, sprint:, project:, text: "Ship dashboard")
    end

    it "renders the goal value" do
      expect(rendered_form).to have_field(Sprint.human_attribute_name(:goal), with: "Ship dashboard")
    end
  end

  context "when the sprint is shared from another project" do
    let(:source_project) { create(:project) }
    let(:sprint) { create(:sprint, project: source_project) }

    it "renders the project-specific label" do
      label = "#{Sprint.human_attribute_name(:goal)} #{I18n.t('backlogs.sprint_form.goal_for_this_project_suffix')}"

      expect(rendered_form).to have_field(
        label
      )
    end

    it "renders the shared sprint caption" do
      expect(rendered_form).to have_text(I18n.t("backlogs.sprint_form.goal_caption"))
    end
  end

  context "when disabled" do
    let(:disabled) { true }

    it "renders the goal field as disabled" do
      expect(rendered_form).to have_field(Sprint.human_attribute_name(:goal), disabled: true)
    end
  end
end
