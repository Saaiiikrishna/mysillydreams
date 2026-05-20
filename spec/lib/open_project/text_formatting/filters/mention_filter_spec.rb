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
require_relative "../markdown/expected_markdown"

RSpec.describe OpenProject::TextFormatting::Filters::MentionFilter do
  include_context "expected markdown modules"

  shared_let(:role) do
    create(:project_role, permissions: %i[view_work_packages])
  end
  shared_let(:project) { create(:project) }
  shared_let(:author) { create(:user, member_with_roles: { project => role }) }

  before { login_as(author) }

  def user_mention(user)
    %(<mention class="mention" data-id="#{user.id}" data-type="user" data-text="@#{user.name}">@#{user.name}</mention>)
  end

  def group_mention(group)
    %(<mention class="mention" data-id="#{group.id}" data-type="group" data-text="@#{group.name}">@#{group.name}</mention>)
  end

  def work_package_mention(work_package)
    id = work_package.id
    %(<mention class="mention" data-id="#{id}" data-type="work_package" data-text="##{id}">##{id}</mention>)
  end

  describe "query count" do
    let!(:users) { create_list(:user, 3, member_with_roles: { project => role }) }
    let!(:groups) { create_list(:group, 2, member_with_roles: { project => role }) }
    let!(:work_packages) { create_list(:work_package, 3, project:, author:) }

    let(:raw) do
      [
        *users.map { user_mention(it) },
        *groups.map { group_mention(it) },
        *work_packages.map { work_package_mention(it) }
      ].join(" ")
    end

    it "fetches each mention class with a single IN-batched SELECT and zero per-record find_bys" do
      recorder = ActiveRecord::QueryRecorder.new { format_text(raw) }

      principal_batched = recorder.log.grep(/SELECT "users"\..*FROM "users".*"users"\."id" IN/i)
      principal_per_record = recorder.log.grep(/SELECT "users"\..*FROM "users".*"users"\."id" = .* LIMIT/i)
      wp_batched = recorder.log.grep(/SELECT "work_packages"\..*FROM "work_packages".*"work_packages"\."id" IN/i)
      wp_per_record = recorder.log.grep(/SELECT "work_packages"\..*FROM "work_packages".*"work_packages"\."id" = .* LIMIT/i)

      # User and Group inherit Principal.visible but apply distinct STI
      # type filters, so the batched form issues one SELECT per class.
      expect(principal_batched.size).to eq(2),
                                        "expected 2 batched principal SELECTs (User + Group), got #{principal_batched.size}:\n" \
                                        "#{principal_batched.join("\n")}"
      expect(wp_batched.size).to eq(1),
                                 "expected 1 batched work_packages SELECT, got #{wp_batched.size}:\n" \
                                 "#{wp_batched.join("\n")}"
      expect(principal_per_record).to be_empty,
                                      "expected zero per-record principal find_bys, got:\n#{principal_per_record.join("\n")}"
      expect(wp_per_record).to be_empty,
                               "expected zero per-record work_package find_bys, got:\n#{wp_per_record.join("\n")}"
    end
  end

  describe "visibility per record" do
    let!(:visible_user) { create(:user, member_with_roles: { project => role }) }
    let!(:invisible_user) { create(:user) } # no project membership, not visible to author

    it "renders visible records as links and falls back to plain text for invisible ones in the same batch" do
      raw = [user_mention(visible_user), user_mention(invisible_user)].join(" ")

      rendered = format_text(raw)

      expect(rendered).to include(%(href="/users/#{visible_user.id}"))
      expect(rendered).not_to include(%(href="/users/#{invisible_user.id}"))
      expect(rendered).to include("@#{invisible_user.name}")
    end
  end

  describe "unknown data-type" do
    it "raises ArgumentError" do
      raw = %(<mention class="mention" data-id="1" data-type="bogus" data-text="@x">@x</mention>)

      expect { format_text(raw) }.to raise_error(ArgumentError)
    end
  end
end
