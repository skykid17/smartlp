import { Tab } from './CustomTab.types';
export type CustomTabInstance<T extends typeof CustomTabBase = typeof CustomTabBase> = InstanceType<T>;
export type CustomTabConstructor<T extends typeof CustomTabBase = typeof CustomTabBase> = new (...args: ConstructorParameters<T>) => CustomTabInstance<T>;
export declare abstract class CustomTabBase {
    protected tab: Tab;
    protected el: HTMLDivElement;
    constructor(tab: Tab, el: HTMLDivElement);
    abstract render(): void;
}
