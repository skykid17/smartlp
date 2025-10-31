import { z } from 'zod';
export declare const alerts: z.ZodOptional<z.ZodArray<z.ZodObject<{
    name: z.ZodString;
    label: z.ZodString;
    description: z.ZodString;
    adaptiveResponse: z.ZodOptional<z.ZodObject<{
        task: z.ZodArray<z.ZodString, "many">;
        supportsAdhoc: z.ZodBoolean;
        supportsCloud: z.ZodBoolean;
        subject: z.ZodArray<z.ZodString, "many">;
        category: z.ZodArray<z.ZodString, "many">;
        technology: z.ZodArray<z.ZodObject<{
            version: z.ZodArray<z.ZodString, "many">;
            product: z.ZodString;
            vendor: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            version: string[];
            product: string;
            vendor: string;
        }, {
            version: string[];
            product: string;
            vendor: string;
        }>, "many">;
        drilldownUri: z.ZodOptional<z.ZodString>;
        sourcetype: z.ZodOptional<z.ZodString>;
    }, "strip", z.ZodTypeAny, {
        task: string[];
        supportsAdhoc: boolean;
        supportsCloud: boolean;
        subject: string[];
        category: string[];
        technology: {
            version: string[];
            product: string;
            vendor: string;
        }[];
        drilldownUri?: string | undefined;
        sourcetype?: string | undefined;
    }, {
        task: string[];
        supportsAdhoc: boolean;
        supportsCloud: boolean;
        subject: string[];
        category: string[];
        technology: {
            version: string[];
            product: string;
            vendor: string;
        }[];
        drilldownUri?: string | undefined;
        sourcetype?: string | undefined;
    }>>;
    entity: z.ZodOptional<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
        type: z.ZodString;
        field: z.ZodString;
        label: z.ZodString;
        help: z.ZodOptional<z.ZodString>;
        tooltip: z.ZodOptional<z.ZodString>;
    }, {
        required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    }>, {
        type: z.ZodLiteral<"text">;
        validators: z.ZodOptional<z.ZodArray<z.ZodUnion<[z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"number">;
            range: z.ZodArray<z.ZodNumber, "many">;
            isInteger: z.ZodOptional<z.ZodBoolean>;
        }, "strip", z.ZodTypeAny, {
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        }, {
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"string">;
            minLength: z.ZodNumber;
            maxLength: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        }, {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"regex">;
            pattern: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        }, {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"email">;
        }, "strip", z.ZodTypeAny, {
            type: "email";
            errorMsg?: string | undefined;
        }, {
            type: "email";
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"ipv4">;
        }, "strip", z.ZodTypeAny, {
            type: "ipv4";
            errorMsg?: string | undefined;
        }, {
            type: "ipv4";
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"url">;
        }, "strip", z.ZodTypeAny, {
            type: "url";
            errorMsg?: string | undefined;
        }, {
            type: "url";
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"date">;
        }, "strip", z.ZodTypeAny, {
            type: "date";
            errorMsg?: string | undefined;
        }, {
            type: "date";
            errorMsg?: string | undefined;
        }>]>, "many">>;
        defaultValue: z.ZodOptional<z.ZodUnion<[z.ZodString, z.ZodNumber, z.ZodBoolean]>>;
        options: z.ZodOptional<z.ZodObject<{
            display: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            disableonEdit: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            enable: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            requiredWhenVisible: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
        }, "strip", z.ZodTypeAny, {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        }, {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        }>>;
        modifyFieldsOnValue: z.ZodOptional<z.ZodArray<z.ZodObject<{
            fieldValue: z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>;
            mode: z.ZodOptional<z.ZodEnum<["create", "edit", "config", "clone"]>>;
            fieldsToModify: z.ZodArray<z.ZodObject<{
                fieldId: z.ZodString;
                display: z.ZodOptional<z.ZodBoolean>;
                value: z.ZodOptional<z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>>;
                disabled: z.ZodOptional<z.ZodBoolean>;
                required: z.ZodOptional<z.ZodBoolean>;
                help: z.ZodOptional<z.ZodString>;
                label: z.ZodOptional<z.ZodString>;
                markdownMessage: z.ZodOptional<z.ZodUnion<[z.ZodObject<{
                    markdownType: z.ZodLiteral<"text">;
                    text: z.ZodString;
                    color: z.ZodOptional<z.ZodString>;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                }, {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                }>, z.ZodObject<{
                    markdownType: z.ZodLiteral<"hybrid">;
                    text: z.ZodString;
                    token: z.ZodString;
                    linkText: z.ZodString;
                    link: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                }, {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                }>, z.ZodObject<{
                    markdownType: z.ZodLiteral<"link">;
                    text: z.ZodString;
                    link: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "link";
                    text: string;
                    link: string;
                }, {
                    markdownType: "link";
                    text: string;
                    link: string;
                }>, z.ZodObject<{
                    markdownType: z.ZodOptional<z.ZodUndefined>;
                    text: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    text: string;
                    markdownType?: undefined;
                }, {
                    text: string;
                    markdownType?: undefined;
                }>]>>;
            }, "strip", z.ZodTypeAny, {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }, {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }>, "many">;
        }, "strip", z.ZodTypeAny, {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }, {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }>, "many">>;
    }>, "strip", z.ZodTypeAny, {
        type: "text";
        label: string;
        field: string;
        options?: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        validators?: ({
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        } | {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        } | {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        } | {
            type: "email";
            errorMsg?: string | undefined;
        } | {
            type: "ipv4";
            errorMsg?: string | undefined;
        } | {
            type: "url";
            errorMsg?: string | undefined;
        } | {
            type: "date";
            errorMsg?: string | undefined;
        })[] | undefined;
        defaultValue?: string | number | boolean | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    }, {
        type: "text";
        label: string;
        field: string;
        options?: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        validators?: ({
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        } | {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        } | {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        } | {
            type: "email";
            errorMsg?: string | undefined;
        } | {
            type: "ipv4";
            errorMsg?: string | undefined;
        } | {
            type: "url";
            errorMsg?: string | undefined;
        } | {
            type: "date";
            errorMsg?: string | undefined;
        })[] | undefined;
        defaultValue?: string | number | boolean | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    }>, z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
        type: z.ZodString;
        field: z.ZodString;
        label: z.ZodString;
        help: z.ZodOptional<z.ZodString>;
        tooltip: z.ZodOptional<z.ZodString>;
    }, {
        required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    }>, {
        type: z.ZodLiteral<"textarea">;
        validators: z.ZodOptional<z.ZodArray<z.ZodUnion<[z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"number">;
            range: z.ZodArray<z.ZodNumber, "many">;
            isInteger: z.ZodOptional<z.ZodBoolean>;
        }, "strip", z.ZodTypeAny, {
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        }, {
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"string">;
            minLength: z.ZodNumber;
            maxLength: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        }, {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"regex">;
            pattern: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        }, {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"email">;
        }, "strip", z.ZodTypeAny, {
            type: "email";
            errorMsg?: string | undefined;
        }, {
            type: "email";
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"ipv4">;
        }, "strip", z.ZodTypeAny, {
            type: "ipv4";
            errorMsg?: string | undefined;
        }, {
            type: "ipv4";
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"url">;
        }, "strip", z.ZodTypeAny, {
            type: "url";
            errorMsg?: string | undefined;
        }, {
            type: "url";
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"date">;
        }, "strip", z.ZodTypeAny, {
            type: "date";
            errorMsg?: string | undefined;
        }, {
            type: "date";
            errorMsg?: string | undefined;
        }>]>, "many">>;
        defaultValue: z.ZodOptional<z.ZodString>;
        options: z.ZodOptional<z.ZodObject<z.objectUtil.extendShape<{
            display: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            disableonEdit: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            enable: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            requiredWhenVisible: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
        }, {
            rowsMin: z.ZodOptional<z.ZodNumber>;
            rowsMax: z.ZodOptional<z.ZodNumber>;
        }>, "strip", z.ZodTypeAny, {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
            rowsMin?: number | undefined;
            rowsMax?: number | undefined;
        }, {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
            rowsMin?: number | undefined;
            rowsMax?: number | undefined;
        }>>;
        modifyFieldsOnValue: z.ZodOptional<z.ZodArray<z.ZodObject<{
            fieldValue: z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>;
            mode: z.ZodOptional<z.ZodEnum<["create", "edit", "config", "clone"]>>;
            fieldsToModify: z.ZodArray<z.ZodObject<{
                fieldId: z.ZodString;
                display: z.ZodOptional<z.ZodBoolean>;
                value: z.ZodOptional<z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>>;
                disabled: z.ZodOptional<z.ZodBoolean>;
                required: z.ZodOptional<z.ZodBoolean>;
                help: z.ZodOptional<z.ZodString>;
                label: z.ZodOptional<z.ZodString>;
                markdownMessage: z.ZodOptional<z.ZodUnion<[z.ZodObject<{
                    markdownType: z.ZodLiteral<"text">;
                    text: z.ZodString;
                    color: z.ZodOptional<z.ZodString>;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                }, {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                }>, z.ZodObject<{
                    markdownType: z.ZodLiteral<"hybrid">;
                    text: z.ZodString;
                    token: z.ZodString;
                    linkText: z.ZodString;
                    link: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                }, {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                }>, z.ZodObject<{
                    markdownType: z.ZodLiteral<"link">;
                    text: z.ZodString;
                    link: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "link";
                    text: string;
                    link: string;
                }, {
                    markdownType: "link";
                    text: string;
                    link: string;
                }>, z.ZodObject<{
                    markdownType: z.ZodOptional<z.ZodUndefined>;
                    text: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    text: string;
                    markdownType?: undefined;
                }, {
                    text: string;
                    markdownType?: undefined;
                }>]>>;
            }, "strip", z.ZodTypeAny, {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }, {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }>, "many">;
        }, "strip", z.ZodTypeAny, {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }, {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }>, "many">>;
    }>, "strip", z.ZodTypeAny, {
        type: "textarea";
        label: string;
        field: string;
        options?: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
            rowsMin?: number | undefined;
            rowsMax?: number | undefined;
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        validators?: ({
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        } | {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        } | {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        } | {
            type: "email";
            errorMsg?: string | undefined;
        } | {
            type: "ipv4";
            errorMsg?: string | undefined;
        } | {
            type: "url";
            errorMsg?: string | undefined;
        } | {
            type: "date";
            errorMsg?: string | undefined;
        })[] | undefined;
        defaultValue?: string | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    }, {
        type: "textarea";
        label: string;
        field: string;
        options?: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
            rowsMin?: number | undefined;
            rowsMax?: number | undefined;
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        validators?: ({
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        } | {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        } | {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        } | {
            type: "email";
            errorMsg?: string | undefined;
        } | {
            type: "ipv4";
            errorMsg?: string | undefined;
        } | {
            type: "url";
            errorMsg?: string | undefined;
        } | {
            type: "date";
            errorMsg?: string | undefined;
        })[] | undefined;
        defaultValue?: string | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    }>, z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
        type: z.ZodString;
        field: z.ZodString;
        label: z.ZodString;
        help: z.ZodOptional<z.ZodString>;
        tooltip: z.ZodOptional<z.ZodString>;
    }, {
        required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    }>, {
        type: z.ZodLiteral<"singleSelect">;
        validators: z.ZodOptional<z.ZodArray<z.ZodUnion<[z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"number">;
            range: z.ZodArray<z.ZodNumber, "many">;
            isInteger: z.ZodOptional<z.ZodBoolean>;
        }, "strip", z.ZodTypeAny, {
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        }, {
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"string">;
            minLength: z.ZodNumber;
            maxLength: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        }, {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"regex">;
            pattern: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        }, {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"email">;
        }, "strip", z.ZodTypeAny, {
            type: "email";
            errorMsg?: string | undefined;
        }, {
            type: "email";
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"ipv4">;
        }, "strip", z.ZodTypeAny, {
            type: "ipv4";
            errorMsg?: string | undefined;
        }, {
            type: "ipv4";
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"url">;
        }, "strip", z.ZodTypeAny, {
            type: "url";
            errorMsg?: string | undefined;
        }, {
            type: "url";
            errorMsg?: string | undefined;
        }>, z.ZodObject<{
            errorMsg: z.ZodOptional<z.ZodString>;
            type: z.ZodLiteral<"date">;
        }, "strip", z.ZodTypeAny, {
            type: "date";
            errorMsg?: string | undefined;
        }, {
            type: "date";
            errorMsg?: string | undefined;
        }>]>, "many">>;
        defaultValue: z.ZodOptional<z.ZodUnion<[z.ZodString, z.ZodNumber, z.ZodBoolean]>>;
        options: z.ZodObject<z.objectUtil.extendShape<{
            display: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            disableonEdit: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            enable: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            requiredWhenVisible: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
        }, {
            disableSearch: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            createSearchChoice: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            referenceName: z.ZodOptional<z.ZodString>;
            endpointUrl: z.ZodOptional<z.ZodString>;
            allowList: z.ZodOptional<z.ZodString>;
            denyList: z.ZodOptional<z.ZodString>;
            labelField: z.ZodOptional<z.ZodString>;
            valueField: z.ZodOptional<z.ZodString>;
            autoCompleteFields: z.ZodOptional<z.ZodArray<z.ZodUnion<[z.ZodObject<{
                value: z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>;
                label: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string | number | boolean;
                label: string;
            }, {
                value: string | number | boolean;
                label: string;
            }>, z.ZodObject<{
                label: z.ZodString;
                children: z.ZodArray<z.ZodObject<{
                    value: z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>;
                    label: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    value: string | number | boolean;
                    label: string;
                }, {
                    value: string | number | boolean;
                    label: string;
                }>, "many">;
            }, "strip", z.ZodTypeAny, {
                label: string;
                children: {
                    value: string | number | boolean;
                    label: string;
                }[];
            }, {
                label: string;
                children: {
                    value: string | number | boolean;
                    label: string;
                }[];
            }>]>, "many">>;
            dependencies: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
            items: z.ZodOptional<z.ZodArray<z.ZodObject<{
                value: z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>;
                label: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string | number | boolean;
                label: string;
            }, {
                value: string | number | boolean;
                label: string;
            }>, "many">>;
        }>, "strip", z.ZodTypeAny, {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
            disableSearch?: boolean | undefined;
            createSearchChoice?: boolean | undefined;
            referenceName?: string | undefined;
            endpointUrl?: string | undefined;
            allowList?: string | undefined;
            denyList?: string | undefined;
            labelField?: string | undefined;
            valueField?: string | undefined;
            autoCompleteFields?: ({
                value: string | number | boolean;
                label: string;
            } | {
                label: string;
                children: {
                    value: string | number | boolean;
                    label: string;
                }[];
            })[] | undefined;
            dependencies?: string[] | undefined;
            items?: {
                value: string | number | boolean;
                label: string;
            }[] | undefined;
        }, {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
            disableSearch?: boolean | undefined;
            createSearchChoice?: boolean | undefined;
            referenceName?: string | undefined;
            endpointUrl?: string | undefined;
            allowList?: string | undefined;
            denyList?: string | undefined;
            labelField?: string | undefined;
            valueField?: string | undefined;
            autoCompleteFields?: ({
                value: string | number | boolean;
                label: string;
            } | {
                label: string;
                children: {
                    value: string | number | boolean;
                    label: string;
                }[];
            })[] | undefined;
            dependencies?: string[] | undefined;
            items?: {
                value: string | number | boolean;
                label: string;
            }[] | undefined;
        }>;
        modifyFieldsOnValue: z.ZodOptional<z.ZodArray<z.ZodObject<{
            fieldValue: z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>;
            mode: z.ZodOptional<z.ZodEnum<["create", "edit", "config", "clone"]>>;
            fieldsToModify: z.ZodArray<z.ZodObject<{
                fieldId: z.ZodString;
                display: z.ZodOptional<z.ZodBoolean>;
                value: z.ZodOptional<z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>>;
                disabled: z.ZodOptional<z.ZodBoolean>;
                required: z.ZodOptional<z.ZodBoolean>;
                help: z.ZodOptional<z.ZodString>;
                label: z.ZodOptional<z.ZodString>;
                markdownMessage: z.ZodOptional<z.ZodUnion<[z.ZodObject<{
                    markdownType: z.ZodLiteral<"text">;
                    text: z.ZodString;
                    color: z.ZodOptional<z.ZodString>;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                }, {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                }>, z.ZodObject<{
                    markdownType: z.ZodLiteral<"hybrid">;
                    text: z.ZodString;
                    token: z.ZodString;
                    linkText: z.ZodString;
                    link: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                }, {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                }>, z.ZodObject<{
                    markdownType: z.ZodLiteral<"link">;
                    text: z.ZodString;
                    link: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "link";
                    text: string;
                    link: string;
                }, {
                    markdownType: "link";
                    text: string;
                    link: string;
                }>, z.ZodObject<{
                    markdownType: z.ZodOptional<z.ZodUndefined>;
                    text: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    text: string;
                    markdownType?: undefined;
                }, {
                    text: string;
                    markdownType?: undefined;
                }>]>>;
            }, "strip", z.ZodTypeAny, {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }, {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }>, "many">;
        }, "strip", z.ZodTypeAny, {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }, {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }>, "many">>;
    }>, "strip", z.ZodTypeAny, {
        options: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
            disableSearch?: boolean | undefined;
            createSearchChoice?: boolean | undefined;
            referenceName?: string | undefined;
            endpointUrl?: string | undefined;
            allowList?: string | undefined;
            denyList?: string | undefined;
            labelField?: string | undefined;
            valueField?: string | undefined;
            autoCompleteFields?: ({
                value: string | number | boolean;
                label: string;
            } | {
                label: string;
                children: {
                    value: string | number | boolean;
                    label: string;
                }[];
            })[] | undefined;
            dependencies?: string[] | undefined;
            items?: {
                value: string | number | boolean;
                label: string;
            }[] | undefined;
        };
        type: "singleSelect";
        label: string;
        field: string;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        validators?: ({
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        } | {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        } | {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        } | {
            type: "email";
            errorMsg?: string | undefined;
        } | {
            type: "ipv4";
            errorMsg?: string | undefined;
        } | {
            type: "url";
            errorMsg?: string | undefined;
        } | {
            type: "date";
            errorMsg?: string | undefined;
        })[] | undefined;
        defaultValue?: string | number | boolean | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    }, {
        options: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
            disableSearch?: boolean | undefined;
            createSearchChoice?: boolean | undefined;
            referenceName?: string | undefined;
            endpointUrl?: string | undefined;
            allowList?: string | undefined;
            denyList?: string | undefined;
            labelField?: string | undefined;
            valueField?: string | undefined;
            autoCompleteFields?: ({
                value: string | number | boolean;
                label: string;
            } | {
                label: string;
                children: {
                    value: string | number | boolean;
                    label: string;
                }[];
            })[] | undefined;
            dependencies?: string[] | undefined;
            items?: {
                value: string | number | boolean;
                label: string;
            }[] | undefined;
        };
        type: "singleSelect";
        label: string;
        field: string;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        validators?: ({
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        } | {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        } | {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        } | {
            type: "email";
            errorMsg?: string | undefined;
        } | {
            type: "ipv4";
            errorMsg?: string | undefined;
        } | {
            type: "url";
            errorMsg?: string | undefined;
        } | {
            type: "date";
            errorMsg?: string | undefined;
        })[] | undefined;
        defaultValue?: string | number | boolean | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    }>, z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
        type: z.ZodString;
        field: z.ZodString;
        label: z.ZodString;
        help: z.ZodOptional<z.ZodString>;
        tooltip: z.ZodOptional<z.ZodString>;
    }, {
        required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    }>, {
        type: z.ZodLiteral<"checkbox">;
        defaultValue: z.ZodOptional<z.ZodUnion<[z.ZodNumber, z.ZodBoolean]>>;
        options: z.ZodOptional<z.ZodObject<{
            display: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            disableonEdit: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            enable: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            requiredWhenVisible: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
        }, "strip", z.ZodTypeAny, {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        }, {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        }>>;
        modifyFieldsOnValue: z.ZodOptional<z.ZodArray<z.ZodObject<{
            fieldValue: z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>;
            mode: z.ZodOptional<z.ZodEnum<["create", "edit", "config", "clone"]>>;
            fieldsToModify: z.ZodArray<z.ZodObject<{
                fieldId: z.ZodString;
                display: z.ZodOptional<z.ZodBoolean>;
                value: z.ZodOptional<z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>>;
                disabled: z.ZodOptional<z.ZodBoolean>;
                required: z.ZodOptional<z.ZodBoolean>;
                help: z.ZodOptional<z.ZodString>;
                label: z.ZodOptional<z.ZodString>;
                markdownMessage: z.ZodOptional<z.ZodUnion<[z.ZodObject<{
                    markdownType: z.ZodLiteral<"text">;
                    text: z.ZodString;
                    color: z.ZodOptional<z.ZodString>;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                }, {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                }>, z.ZodObject<{
                    markdownType: z.ZodLiteral<"hybrid">;
                    text: z.ZodString;
                    token: z.ZodString;
                    linkText: z.ZodString;
                    link: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                }, {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                }>, z.ZodObject<{
                    markdownType: z.ZodLiteral<"link">;
                    text: z.ZodString;
                    link: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "link";
                    text: string;
                    link: string;
                }, {
                    markdownType: "link";
                    text: string;
                    link: string;
                }>, z.ZodObject<{
                    markdownType: z.ZodOptional<z.ZodUndefined>;
                    text: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    text: string;
                    markdownType?: undefined;
                }, {
                    text: string;
                    markdownType?: undefined;
                }>]>>;
            }, "strip", z.ZodTypeAny, {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }, {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }>, "many">;
        }, "strip", z.ZodTypeAny, {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }, {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }>, "many">>;
    }>, "strip", z.ZodTypeAny, {
        type: "checkbox";
        label: string;
        field: string;
        options?: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        defaultValue?: number | boolean | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    }, {
        type: "checkbox";
        label: string;
        field: string;
        options?: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        defaultValue?: number | boolean | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    }>, z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
        type: z.ZodString;
        field: z.ZodString;
        label: z.ZodString;
        help: z.ZodOptional<z.ZodString>;
        tooltip: z.ZodOptional<z.ZodString>;
    }, {
        required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    }>, {
        type: z.ZodLiteral<"radio">;
        defaultValue: z.ZodOptional<z.ZodString>;
        options: z.ZodObject<z.objectUtil.extendShape<{
            display: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            disableonEdit: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            enable: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            requiredWhenVisible: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
        }, {
            items: z.ZodArray<z.ZodObject<{
                value: z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>;
                label: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string | number | boolean;
                label: string;
            }, {
                value: string | number | boolean;
                label: string;
            }>, "many">;
        }>, "strip", z.ZodTypeAny, {
            items: {
                value: string | number | boolean;
                label: string;
            }[];
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        }, {
            items: {
                value: string | number | boolean;
                label: string;
            }[];
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        }>;
        modifyFieldsOnValue: z.ZodOptional<z.ZodArray<z.ZodObject<{
            fieldValue: z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>;
            mode: z.ZodOptional<z.ZodEnum<["create", "edit", "config", "clone"]>>;
            fieldsToModify: z.ZodArray<z.ZodObject<{
                fieldId: z.ZodString;
                display: z.ZodOptional<z.ZodBoolean>;
                value: z.ZodOptional<z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>>;
                disabled: z.ZodOptional<z.ZodBoolean>;
                required: z.ZodOptional<z.ZodBoolean>;
                help: z.ZodOptional<z.ZodString>;
                label: z.ZodOptional<z.ZodString>;
                markdownMessage: z.ZodOptional<z.ZodUnion<[z.ZodObject<{
                    markdownType: z.ZodLiteral<"text">;
                    text: z.ZodString;
                    color: z.ZodOptional<z.ZodString>;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                }, {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                }>, z.ZodObject<{
                    markdownType: z.ZodLiteral<"hybrid">;
                    text: z.ZodString;
                    token: z.ZodString;
                    linkText: z.ZodString;
                    link: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                }, {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                }>, z.ZodObject<{
                    markdownType: z.ZodLiteral<"link">;
                    text: z.ZodString;
                    link: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    markdownType: "link";
                    text: string;
                    link: string;
                }, {
                    markdownType: "link";
                    text: string;
                    link: string;
                }>, z.ZodObject<{
                    markdownType: z.ZodOptional<z.ZodUndefined>;
                    text: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    text: string;
                    markdownType?: undefined;
                }, {
                    text: string;
                    markdownType?: undefined;
                }>]>>;
            }, "strip", z.ZodTypeAny, {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }, {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }>, "many">;
        }, "strip", z.ZodTypeAny, {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }, {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }>, "many">>;
    }>, "strip", z.ZodTypeAny, {
        options: {
            items: {
                value: string | number | boolean;
                label: string;
            }[];
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        };
        type: "radio";
        label: string;
        field: string;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        defaultValue?: string | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    }, {
        options: {
            items: {
                value: string | number | boolean;
                label: string;
            }[];
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        };
        type: "radio";
        label: string;
        field: string;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        defaultValue?: string | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    }>, z.ZodObject<z.objectUtil.extendShape<{
        type: z.ZodString;
        field: z.ZodString;
        label: z.ZodString;
        help: z.ZodOptional<z.ZodString>;
        tooltip: z.ZodOptional<z.ZodString>;
    }, {
        type: z.ZodLiteral<"singleSelectSplunkSearch">;
        defaultValue: z.ZodOptional<z.ZodUnion<[z.ZodString, z.ZodNumber, z.ZodBoolean]>>;
        search: z.ZodOptional<z.ZodString>;
        valueField: z.ZodOptional<z.ZodString>;
        labelField: z.ZodOptional<z.ZodString>;
        options: z.ZodOptional<z.ZodObject<{
            items: z.ZodArray<z.ZodObject<{
                value: z.ZodUnion<[z.ZodNumber, z.ZodString, z.ZodBoolean]>;
                label: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string | number | boolean;
                label: string;
            }, {
                value: string | number | boolean;
                label: string;
            }>, "many">;
        }, "strip", z.ZodTypeAny, {
            items: {
                value: string | number | boolean;
                label: string;
            }[];
        }, {
            items: {
                value: string | number | boolean;
                label: string;
            }[];
        }>>;
    }>, "strip", z.ZodTypeAny, {
        type: "singleSelectSplunkSearch";
        label: string;
        field: string;
        options?: {
            items: {
                value: string | number | boolean;
                label: string;
            }[];
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        defaultValue?: string | number | boolean | undefined;
        labelField?: string | undefined;
        valueField?: string | undefined;
        search?: string | undefined;
    }, {
        type: "singleSelectSplunkSearch";
        label: string;
        field: string;
        options?: {
            items: {
                value: string | number | boolean;
                label: string;
            }[];
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        defaultValue?: string | number | boolean | undefined;
        labelField?: string | undefined;
        valueField?: string | undefined;
        search?: string | undefined;
    }>]>, "many">>;
}, "strip", z.ZodTypeAny, {
    name: string;
    label: string;
    description: string;
    entity?: ({
        type: "text";
        label: string;
        field: string;
        options?: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        validators?: ({
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        } | {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        } | {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        } | {
            type: "email";
            errorMsg?: string | undefined;
        } | {
            type: "ipv4";
            errorMsg?: string | undefined;
        } | {
            type: "url";
            errorMsg?: string | undefined;
        } | {
            type: "date";
            errorMsg?: string | undefined;
        })[] | undefined;
        defaultValue?: string | number | boolean | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    } | {
        type: "textarea";
        label: string;
        field: string;
        options?: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
            rowsMin?: number | undefined;
            rowsMax?: number | undefined;
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        validators?: ({
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        } | {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        } | {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        } | {
            type: "email";
            errorMsg?: string | undefined;
        } | {
            type: "ipv4";
            errorMsg?: string | undefined;
        } | {
            type: "url";
            errorMsg?: string | undefined;
        } | {
            type: "date";
            errorMsg?: string | undefined;
        })[] | undefined;
        defaultValue?: string | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    } | {
        options: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
            disableSearch?: boolean | undefined;
            createSearchChoice?: boolean | undefined;
            referenceName?: string | undefined;
            endpointUrl?: string | undefined;
            allowList?: string | undefined;
            denyList?: string | undefined;
            labelField?: string | undefined;
            valueField?: string | undefined;
            autoCompleteFields?: ({
                value: string | number | boolean;
                label: string;
            } | {
                label: string;
                children: {
                    value: string | number | boolean;
                    label: string;
                }[];
            })[] | undefined;
            dependencies?: string[] | undefined;
            items?: {
                value: string | number | boolean;
                label: string;
            }[] | undefined;
        };
        type: "singleSelect";
        label: string;
        field: string;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        validators?: ({
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        } | {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        } | {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        } | {
            type: "email";
            errorMsg?: string | undefined;
        } | {
            type: "ipv4";
            errorMsg?: string | undefined;
        } | {
            type: "url";
            errorMsg?: string | undefined;
        } | {
            type: "date";
            errorMsg?: string | undefined;
        })[] | undefined;
        defaultValue?: string | number | boolean | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    } | {
        type: "checkbox";
        label: string;
        field: string;
        options?: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        defaultValue?: number | boolean | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    } | {
        options: {
            items: {
                value: string | number | boolean;
                label: string;
            }[];
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        };
        type: "radio";
        label: string;
        field: string;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        defaultValue?: string | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    } | {
        type: "singleSelectSplunkSearch";
        label: string;
        field: string;
        options?: {
            items: {
                value: string | number | boolean;
                label: string;
            }[];
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        defaultValue?: string | number | boolean | undefined;
        labelField?: string | undefined;
        valueField?: string | undefined;
        search?: string | undefined;
    })[] | undefined;
    adaptiveResponse?: {
        task: string[];
        supportsAdhoc: boolean;
        supportsCloud: boolean;
        subject: string[];
        category: string[];
        technology: {
            version: string[];
            product: string;
            vendor: string;
        }[];
        drilldownUri?: string | undefined;
        sourcetype?: string | undefined;
    } | undefined;
}, {
    name: string;
    label: string;
    description: string;
    entity?: ({
        type: "text";
        label: string;
        field: string;
        options?: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        validators?: ({
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        } | {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        } | {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        } | {
            type: "email";
            errorMsg?: string | undefined;
        } | {
            type: "ipv4";
            errorMsg?: string | undefined;
        } | {
            type: "url";
            errorMsg?: string | undefined;
        } | {
            type: "date";
            errorMsg?: string | undefined;
        })[] | undefined;
        defaultValue?: string | number | boolean | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    } | {
        type: "textarea";
        label: string;
        field: string;
        options?: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
            rowsMin?: number | undefined;
            rowsMax?: number | undefined;
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        validators?: ({
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        } | {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        } | {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        } | {
            type: "email";
            errorMsg?: string | undefined;
        } | {
            type: "ipv4";
            errorMsg?: string | undefined;
        } | {
            type: "url";
            errorMsg?: string | undefined;
        } | {
            type: "date";
            errorMsg?: string | undefined;
        })[] | undefined;
        defaultValue?: string | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    } | {
        options: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
            disableSearch?: boolean | undefined;
            createSearchChoice?: boolean | undefined;
            referenceName?: string | undefined;
            endpointUrl?: string | undefined;
            allowList?: string | undefined;
            denyList?: string | undefined;
            labelField?: string | undefined;
            valueField?: string | undefined;
            autoCompleteFields?: ({
                value: string | number | boolean;
                label: string;
            } | {
                label: string;
                children: {
                    value: string | number | boolean;
                    label: string;
                }[];
            })[] | undefined;
            dependencies?: string[] | undefined;
            items?: {
                value: string | number | boolean;
                label: string;
            }[] | undefined;
        };
        type: "singleSelect";
        label: string;
        field: string;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        validators?: ({
            type: "number";
            range: number[];
            errorMsg?: string | undefined;
            isInteger?: boolean | undefined;
        } | {
            type: "string";
            minLength: number;
            maxLength: number;
            errorMsg?: string | undefined;
        } | {
            type: "regex";
            pattern: string;
            errorMsg?: string | undefined;
        } | {
            type: "email";
            errorMsg?: string | undefined;
        } | {
            type: "ipv4";
            errorMsg?: string | undefined;
        } | {
            type: "url";
            errorMsg?: string | undefined;
        } | {
            type: "date";
            errorMsg?: string | undefined;
        })[] | undefined;
        defaultValue?: string | number | boolean | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    } | {
        type: "checkbox";
        label: string;
        field: string;
        options?: {
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        defaultValue?: number | boolean | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    } | {
        options: {
            items: {
                value: string | number | boolean;
                label: string;
            }[];
            display?: boolean | undefined;
            disableonEdit?: boolean | undefined;
            enable?: boolean | undefined;
            requiredWhenVisible?: boolean | undefined;
            hideForPlatform?: "cloud" | "enterprise" | undefined;
        };
        type: "radio";
        label: string;
        field: string;
        help?: string | undefined;
        tooltip?: string | undefined;
        required?: boolean | undefined;
        encrypted?: boolean | undefined;
        defaultValue?: string | undefined;
        modifyFieldsOnValue?: {
            fieldValue: string | number | boolean;
            fieldsToModify: {
                fieldId: string;
                value?: string | number | boolean | undefined;
                label?: string | undefined;
                help?: string | undefined;
                required?: boolean | undefined;
                display?: boolean | undefined;
                disabled?: boolean | undefined;
                markdownMessage?: {
                    markdownType: "text";
                    text: string;
                    color?: string | undefined;
                } | {
                    markdownType: "hybrid";
                    text: string;
                    token: string;
                    linkText: string;
                    link: string;
                } | {
                    markdownType: "link";
                    text: string;
                    link: string;
                } | {
                    text: string;
                    markdownType?: undefined;
                } | undefined;
            }[];
            mode?: "clone" | "create" | "edit" | "config" | undefined;
        }[] | undefined;
    } | {
        type: "singleSelectSplunkSearch";
        label: string;
        field: string;
        options?: {
            items: {
                value: string | number | boolean;
                label: string;
            }[];
        } | undefined;
        help?: string | undefined;
        tooltip?: string | undefined;
        defaultValue?: string | number | boolean | undefined;
        labelField?: string | undefined;
        valueField?: string | undefined;
        search?: string | undefined;
    })[] | undefined;
    adaptiveResponse?: {
        task: string[];
        supportsAdhoc: boolean;
        supportsCloud: boolean;
        subject: string[];
        category: string[];
        technology: {
            version: string[];
            product: string;
            vendor: string;
        }[];
        drilldownUri?: string | undefined;
        sourcetype?: string | undefined;
    } | undefined;
}>, "many">>;
