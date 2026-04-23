//-- copyright
// OpenProject is an open source project management software.
// Copyright (C) the OpenProject GmbH
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License version 3.
//
// OpenProject is a fork of ChiliProject, which is a fork of Redmine. The copyright follows:
// Copyright (C) 2006-2013 Jean-Philippe Lang
// Copyright (C) 2010-2013 the ChiliProject Team
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
//
// See COPYRIGHT and LICENSE files for more details.
//++

import { createExtension } from '@blocknote/core';
import { Plugin, PluginKey } from 'prosemirror-state';
import { Decoration, DecorationSet } from 'prosemirror-view';
import type { Node as PmNode, Mark } from 'prosemirror-model';
import { isHrefExternal } from 'core-stimulus/helpers/external-link-helpers';

const pluginKey = new PluginKey('externalLinkA11y');
const DESCRIPTION_ID = 'open-blank-target-link-description';

function findExternalLinkMark(node:PmNode):Mark|null {
  for (const mark of node.marks) {
    if (mark.type.name === 'link' && isHrefExternal(String(mark.attrs.href ?? ''))) {
      return mark;
    }
  }
  return null;
}

// Detects whether the next inline node belongs to the same contiguous link
// run. Assumes every inline node inside a link carries the link mark. This
// holds for the current BlockNote schema, which has no inline custom nodes
// that opt out of marks. If a mention/inline-embed node is ever added that
// permits a link mark to wrap it without inheriting, revisit this — you will
// need to walk link runs explicitly instead of relying on nodeAfter.
function sameLinkContinues(next:PmNode|null|undefined, href:string):boolean {
  if (!next) return false;
  return next.marks.some(
    (m) => m.type.name === 'link' && String(m.attrs.href ?? '') === href,
  );
}

let missingDescriptionWarned = false;

function readDescription():string {
  const source = document.getElementById(DESCRIPTION_ID);
  const text = source?.textContent?.trim() ?? '';
  if (!text && !missingDescriptionWarned) {
    missingDescriptionWarned = true;
    // The sr-only span is rendered in base.html.erb and also referenced by
    // ExternalLinksController. If it goes missing, external-link hints silently
    // become empty — warn once so the regression surfaces during development.
    console.warn(
      `[ExternalLinkA11yExtension] #${DESCRIPTION_ID} not found; external-link hints will be empty.`,
    );
  }
  return text;
}

function buildWidget():HTMLElement {
  const span = document.createElement('span');
  span.className = 'sr-only';
  // contenteditable=false keeps the hint inert inside ProseMirror's editable
  // region, so users cannot place their caret inside it or delete it.
  span.setAttribute('contenteditable', 'false');
  // Reuse the same translated string the body-level ExternalLinksController
  // references via aria-describedby, keeping i18n centralised in Rails.
  span.textContent = readDescription();
  return span;
}

function buildDecorations(doc:PmNode):DecorationSet {
  const decorations:Decoration[] = [];

  doc.descendants((node, pos) => {
    const linkMark = findExternalLinkMark(node);
    if (!linkMark) return;

    const href = String(linkMark.attrs.href ?? '');
    const end = pos + node.nodeSize;
    const next = doc.resolve(end).nodeAfter;

    // Only emit the hint at the end of a contiguous link run. Adjacent inline
    // nodes (e.g. text with an extra bold mark) carrying the same href are
    // rendered as one <a>, so we emit a single hint per link, not per node.
    if (sameLinkContinues(next, href)) return;

    decorations.push(
      Decoration.widget(end, buildWidget, {
        // Wrap the widget in the link mark so the sr-only span is rendered
        // INSIDE the <a> tag. This makes the hint part of the link's
        // accessible name — the only approach that is reliably announced by
        // VoiceOver/NVDA in a contenteditable context, where aria-describedby
        // is widely ignored.
        marks: [linkMark],
        // Negative side keeps the widget attached to the preceding link run
        // when content is inserted at the same position.
        side: -1,
        ignoreSelection: true,
      }),
    );
  });

  return DecorationSet.create(doc, decorations);
}

/**
 * BlockNote extension that adds a screen-reader-only "opens in new tab" hint
 * to external links inside the editor.
 *
 * The hint is injected as a ProseMirror widget decoration wrapped in the link
 * mark, so the resulting DOM looks like:
 *
 *   <a href="..." target="_blank" rel="...">
 *     Link text
 *     <span class="sr-only" contenteditable="false">Open link in a new tab</span>
 *   </a>
 *
 * Putting the text inside the anchor makes it part of the link's accessible
 * name, which screen readers announce in every mode — including the edit mode
 * they switch into inside contenteditable regions. The previous approach of
 * using `aria-describedby` on an inline decoration span did not work in
 * contenteditable: VoiceOver and NVDA ignore aria-describedby there, and the
 * inline decoration landed the attribute on a generic span rather than the
 * anchor anyway.
 *
 * Decorations never mutate the document model, so ProseMirror does not
 * re-render and there is no DOMObserver mutation loop (the reason direct DOM
 * rewriting was abandoned for this attribute).
 */
export const ExternalLinkA11yExtension = createExtension({
  key: 'externalLinkA11y',

  prosemirrorPlugins: [
    new Plugin({
      key: pluginKey,
      state: {
        init(_, { doc }) {
          return buildDecorations(doc);
        },
        apply(tr, oldDecos) {
          if (tr.docChanged) {
            return buildDecorations(tr.doc);
          }
          return oldDecos.map(tr.mapping, tr.doc);
        },
      },
      props: {
        decorations(state) {
          return pluginKey.getState(state) as DecorationSet;
        },
      },
    }),
  ],
});
