import React from 'react';
import { z } from 'zod';
import { MarkdownMessageType } from '../../types/globalConfig/entities';
export type MarkdownMessageProps = z.infer<typeof MarkdownMessageType>;
declare function MarkdownMessage(props: MarkdownMessageProps): React.JSX.Element;
declare const _default: React.MemoExoticComponent<typeof MarkdownMessage>;
export default _default;
