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

import {
  attachClosestEdge,
  type Edge,
  extractClosestEdge,
} from '@atlaskit/pragmatic-drag-and-drop-hitbox/closest-edge';
import { combine } from '@atlaskit/pragmatic-drag-and-drop/combine';
import { draggable, dropTargetForElements } from '@atlaskit/pragmatic-drag-and-drop/element/adapter';
import { setCustomNativeDragPreview } from '@atlaskit/pragmatic-drag-and-drop/element/set-custom-native-drag-preview';
import { preventUnhandled } from '@atlaskit/pragmatic-drag-and-drop/prevent-unhandled';
import { Controller } from '@hotwired/stimulus';
import { attributeTokenList } from 'core-app/shared/helpers/dom-helpers';
import { closestInteractiveElement } from 'core-stimulus/helpers/interactive-element-helper';
import {
  isSortableItemData,
  sortableItemSelector,
  sortableItemData,
  sortableListsMovingAttribute,
  sortableListsRootSelector,
  type SortableItemData,
} from './drag-and-drop';

type CleanupFn = () => void;

export default class ItemController extends Controller<HTMLElement> {
  static targets = ['handle', 'preview'];

  static values = {
    id: String,
    moveUrl: String,
    type: { type: String, default: 'item' },
  };

  declare idValue:string;
  declare moveUrlValue:string;
  declare typeValue:string;

  declare readonly handleTarget:HTMLElement;
  declare readonly hasHandleTarget:boolean;
  declare readonly previewTarget:HTMLElement;

  private cleanupFn?:CleanupFn;
  private dropIndicatorElement?:HTMLElement;
  private readonly refreshAfterMorphBound = this.refreshAfterMorph.bind(this);
  private static nextDescriptionId = 0;

  connect() {
    this.cleanupFn = combine(
      this.registerHandleAccessibility(),
      this.registerDraggable(),
      this.registerDropTarget(),
      this.registerTurboMorphRefresh(),
    );
  }

  disconnect() {
    this.cleanupFn?.();
    this.cleanupFn = undefined;
  }

  private renderDropIndicator(edge:Edge|null) {
    const currentEdge = this.dropIndicatorElement?.dataset.dropPosition;
    const currentOwner = this.dropIndicatorElement?.dataset.dropPositionOwner;
    const nextIndicator = edge ? this.resolveDropIndicator(edge) : null;

    if (
      currentOwner === this.idValue &&
      nextIndicator &&
      this.dropIndicatorElement === nextIndicator.element &&
      currentEdge === nextIndicator.edge
    ) {
      return;
    }

    this.clearDropIndicator();

    if (nextIndicator) {
      this.dropIndicatorElement = nextIndicator.element;
      nextIndicator.element.dataset.dropPosition = nextIndicator.edge;
      nextIndicator.element.dataset.dropPositionOwner = this.idValue;
    }
  }

  private clearDropIndicator() {
    if (!this.dropIndicatorElement) {
      return;
    }

    if (this.dropIndicatorElement.dataset.dropPositionOwner === this.idValue) {
      delete this.dropIndicatorElement.dataset.dropPosition;
      delete this.dropIndicatorElement.dataset.dropPositionOwner;
    }

    this.dropIndicatorElement = undefined;
  }

  private resolveDropIndicator(edge:Edge):{ element:HTMLElement; edge:Edge } {
    if (edge !== 'bottom') {
      return { element: this.element, edge };
    }

    const nextItem = this.element.nextElementSibling;

    if (
      nextItem instanceof HTMLElement &&
      nextItem.matches(sortableItemSelector) &&
      !nextItem.hasAttribute('data-dragging')
    ) {
      return { element: nextItem, edge: 'top' };
    }

    return { element: this.element, edge };
  }

  private getItemData():SortableItemData {
    return sortableItemData({
      itemId: this.idValue,
      moveUrl: this.moveUrlValue || undefined,
      type: this.typeValue,
    });
  }

  private registerDraggable():CleanupFn {
    return draggable({
      element: this.element,
      ...(this.hasHandleTarget ? { dragHandle: this.handleTarget } : {}),
      canDrag: ({ input }) => this.canDragFromPoint(input.clientX, input.clientY),
      getInitialData: () => this.getItemData(),
      onDragStart: () => {
        preventUnhandled.start();
        this.element.setAttribute('data-dragging', 'source');
      },
      onDrop: () => {
        preventUnhandled.stop();
        this.clearDropIndicator();
        this.element.removeAttribute('data-dragging');
      },
      onGenerateDragPreview: ({ nativeSetDragImage }) => {
        setCustomNativeDragPreview({
          nativeSetDragImage,
          render: ({ container }) => this.renderPreview(container),
        });
      },
    });
  }

  private canDragFromPoint(clientX:number, clientY:number):boolean {
    if (this.element.closest(sortableListsRootSelector)?.hasAttribute(sortableListsMovingAttribute)) {
      return false;
    }

    const target = this.element.ownerDocument.elementFromPoint(clientX, clientY);

    if (!(target instanceof Element) || !this.element.contains(target)) {
      return true;
    }

    const dragHandle = this.hasHandleTarget ? this.handleTarget : this.element;

    return closestInteractiveElement(target, dragHandle) == null;
  }

  private renderPreview(container:HTMLElement) {
    const previewWidth = this.previewTarget.getBoundingClientRect().width;
    const preview = this.previewTarget.cloneNode(true) as HTMLElement;

    this.sanitizePreview(preview);
    preview.setAttribute('data-preview', '');

    if (previewWidth > 0) {
      preview.style.width = `${previewWidth}px`;
    }

    container.append(preview);
  }

  private sanitizePreview(element:HTMLElement) {
    const nodes = [element, ...Array.from(element.querySelectorAll<HTMLElement>('*'))];

    for (const node of nodes) {
      node.removeAttribute('data-controller');
      node.removeAttribute('data-action');
      node.removeAttribute('data-dragging');
      node.removeAttribute('data-drop-position');
      node.removeAttribute('data-drop-position-owner');
      node.removeAttribute('aria-describedby');
      node.removeAttribute('aria-disabled');
      node.removeAttribute('aria-roledescription');

      for (const attribute of Array.from(node.attributes)) {
        if (/^data-.+--.+-target$/.test(attribute.name)) {
          node.removeAttribute(attribute.name);
        }
      }
    }
  }

  private registerDropTarget():CleanupFn {
    return dropTargetForElements({
      element: this.element,
      canDrop: ({ source }) => {
        return isSortableItemData(source.data) && source.data.itemId !== this.idValue;
      },
      getData: ({ input }) => {
        return attachClosestEdge(this.getItemData(), {
          element: this.element,
          input,
          allowedEdges: ['top', 'bottom'],
        });
      },
      getIsSticky: () => true,
      onDragEnter: ({ self }) => {
        const closestEdge = extractClosestEdge(self.data);
        this.renderDropIndicator(closestEdge);
      },
      onDrag: ({ self }) => {
        const closestEdge = extractClosestEdge(self.data);
        this.renderDropIndicator(closestEdge);
      },
      onDragLeave: () => {
        this.clearDropIndicator();
      },
      onDrop: () => {
        this.clearDropIndicator();
      },
    });
  }

  private registerHandleAccessibility():CleanupFn {
    if (!this.hasHandleTarget) {
      return () => undefined;
    }

    const handle = this.handleTarget;
    const restoreHandleAttributes = this.captureAttributes(handle, [
      'aria-describedby',
      'aria-disabled',
      'aria-roledescription',
    ]);
    const description = this.createHandleDescription();
    const root = this.element.closest(sortableListsRootSelector);
    const observer = root ? new MutationObserver(() => this.updateHandleDisabled(handle)) : undefined;

    this.element.append(description);
    handle.setAttribute('aria-roledescription', 'draggable');
    this.addDescriptionReference(handle, description.id);
    this.updateHandleDisabled(handle);
    if (observer && root) {
      observer.observe(root, {
        attributeFilter: [sortableListsMovingAttribute],
        attributes: true,
      });
    }

    return () => {
      observer?.disconnect();
      description.remove();
      restoreHandleAttributes();
    };
  }

  private captureAttributes(element:HTMLElement, attributes:string[]):CleanupFn {
    const originalAttributes = new Map(attributes.map((attribute) => [
      attribute,
      element.getAttribute(attribute),
    ]));

    return () => {
      originalAttributes.forEach((value, attribute) => {
        if (value === null) {
          element.removeAttribute(attribute);
        } else {
          element.setAttribute(attribute, value);
        }
      });
    };
  }

  private createHandleDescription():HTMLElement {
    const description = document.createElement('span');
    const id = ItemController.nextDescriptionId += 1;

    description.id = `sortable-lists-drag-handle-instructions-${id}`;
    description.classList.add('sr-only');
    description.textContent = this.dragHandleInstructions;

    return description;
  }

  private addDescriptionReference(element:HTMLElement, descriptionId:string):void {
    attributeTokenList(element, 'aria-describedby').add(descriptionId);
  }

  private updateHandleDisabled(handle:HTMLElement):void {
    handle.setAttribute(
      'aria-disabled',
      this.element.closest(sortableListsRootSelector)?.hasAttribute(sortableListsMovingAttribute) ? 'true' : 'false',
    );
  }

  private get dragHandleInstructions():string {
    const key = 'js.sortable_lists.drag_handle.instructions';
    const translation = I18n.t(key);

    return translation === key || translation.startsWith('[missing ') ? 'Drag to reposition this item.' : translation;
  }

  private registerTurboMorphRefresh():CleanupFn {
    document.addEventListener('turbo:morph-element', this.refreshAfterMorphBound);

    return () => {
      document.removeEventListener('turbo:morph-element', this.refreshAfterMorphBound);
    };
  }

  private refreshAfterMorph(event:Event) {
    if (event.target !== this.element) {
      return;
    }

    this.disconnect();
    this.connect();
  }
}
