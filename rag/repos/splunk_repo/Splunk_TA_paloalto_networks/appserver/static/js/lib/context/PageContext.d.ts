import React, { ReactNode } from 'react';
import { Platforms } from '../types/globalConfig/pages';
export type PageContextProviderType = {
    platform: Platforms;
};
declare const PageContext: React.Context<PageContextProviderType | undefined>;
export declare function PageContextProvider({ children, platform, }: {
    children: ReactNode;
    platform: Platforms;
}): React.JSX.Element;
export default PageContext;
