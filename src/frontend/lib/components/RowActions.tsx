import { t } from '@lingui/core/macro';
import { ActionIcon, Menu, Tooltip } from '@mantine/core';
import {
  IconArrowRight,
  IconCircleX,
  IconCopy,
  IconDots,
  IconEdit,
  IconTrash
} from '@tabler/icons-react';
import { type ReactNode, useMemo, useState } from 'react';
import { cancelEvent } from '../functions/Events';
import { getDetailUrl } from '../functions/Navigation';
import { navigateToLink } from '../functions/Navigation';
import type { RowAction, RowViewProps } from '../types/Tables';

export type { RowAction, RowViewProps } from '../types/Tables';

// Component for viewing a row in a table
export function RowViewAction(props: RowViewProps): RowAction {
  return {
    ...props,
    color: undefined,
    icon: <IconArrowRight />,
    onClick: (event: any) => {
      const url = getDetailUrl(props.modelType, props.modelId);
      navigateToLink(url, props.navigate, event);
    }
  };
}

// Component for duplicating a row in a table
export function RowDuplicateAction(props: RowAction): RowAction {
  return {
    ...props,
    title: t`Duplicate`,
    color: 'green',
    icon: <IconCopy />
  };
}

// Component for editing a row in a table
export function RowEditAction(props: RowAction): RowAction {
  return {
    ...props,
    title: t`Edit`,
    color: 'blue',
    icon: <IconEdit />
  };
}

// Component for deleting a row in a table
export function RowDeleteAction(props: RowAction): RowAction {
  return {
    ...props,
    title: t`Delete`,
    color: 'red',
    icon: <IconTrash />
  };
}

// Component for cancelling a row in a table
export function RowCancelAction(props: RowAction): RowAction {
  return {
    ...props,
    title: t`Cancel`,
    color: 'red',
    icon: <IconCircleX />
  };
}

/**
 * Component for displaying actions for a row in a table.
 * Displays a simple dropdown menu with a list of actions.
 */
export function RowActions({
  title,
  actions,
  disabled = false,
  index
}: {
  title?: string;
  disabled?: boolean;
  actions: RowAction[];
  index?: number;
}): ReactNode {
  // Prevent default event handling
  // Ref: https://icflorescu.github.io/mantine-datatable/examples/links-or-buttons-inside-clickable-rows-or-cells
  function openMenu(event: any) {
    cancelEvent(event);
    setOpened(!opened);
  }

  const [opened, setOpened] = useState(false);

  const visibleActions = useMemo(() => {
    return actions.filter((action) => !action.hidden);
  }, [actions]);

  // Render a single action icon
  function RowActionIcon(action: Readonly<RowAction>) {
    return (
      <Tooltip
        withinPortal={true}
        label={action.tooltip ?? action.title}
        key={action.title}
        position='left'
      >
        <Menu.Item
          color={action.color}
          leftSection={action.icon}
          onClick={(event) => {
            // Prevent clicking on the action from selecting the row itself
            cancelEvent(event);
            action.onClick?.(event);
            setOpened(false);
          }}
          disabled={action.disabled || false}
        >
          {action.title}
        </Menu.Item>
      </Tooltip>
    );
  }

  return (
    visibleActions.length > 0 && (
      <Menu
        withinPortal={true}
        disabled={disabled}
        position='bottom-end'
        opened={opened}
        onChange={setOpened}
      >
        <Menu.Target>
          <Tooltip withinPortal={true} label={title || t`Actions`}>
            <ActionIcon
              key={`row-action-menu-${index ?? ''}`}
              aria-label={`row-action-menu-${index ?? ''}`}
              onClick={openMenu}
              disabled={disabled}
              variant='subtle'
              color='gray'
            >
              <IconDots />
            </ActionIcon>
          </Tooltip>
        </Menu.Target>
        <Menu.Dropdown>
          {visibleActions.map((action) => (
            <RowActionIcon key={action.title} {...action} />
          ))}
        </Menu.Dropdown>
      </Menu>
    )
  );
}
