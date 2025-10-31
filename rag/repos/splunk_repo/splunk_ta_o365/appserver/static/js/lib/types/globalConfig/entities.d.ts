import { z } from 'zod';
export declare const MarkdownMessageText: z.ZodObject<{
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
}>;
export declare const MarkdownMessageHybrid: z.ZodObject<{
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
}>;
export declare const MarkdownMessageLink: z.ZodObject<{
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
}>;
export declare const MarkdownMessagePlaintext: z.ZodObject<{
    markdownType: z.ZodOptional<z.ZodUndefined>;
    text: z.ZodString;
}, "strip", z.ZodTypeAny, {
    text: string;
    markdownType?: undefined;
}, {
    text: string;
    markdownType?: undefined;
}>;
export declare const MarkdownMessageType: z.ZodUnion<[z.ZodObject<{
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
}>]>;
export declare const LinkEntity: z.ZodObject<z.objectUtil.extendShape<{
    type: z.ZodString;
    field: z.ZodString;
    label: z.ZodString;
    help: z.ZodOptional<z.ZodString>;
    tooltip: z.ZodOptional<z.ZodString>;
}, {
    type: z.ZodLiteral<"helpLink">;
    label: z.ZodOptional<z.ZodString>;
    options: z.ZodObject<{
        text: z.ZodString;
        link: z.ZodString;
        hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
    }, "strip", z.ZodTypeAny, {
        text: string;
        link: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    }, {
        text: string;
        link: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    }>;
    required: z.ZodOptional<z.ZodDefault<z.ZodLiteral<false>>>;
}>, "strip", z.ZodTypeAny, {
    options: {
        text: string;
        link: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    };
    type: "helpLink";
    field: string;
    label?: string | undefined;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: false | undefined;
}, {
    options: {
        text: string;
        link: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    };
    type: "helpLink";
    field: string;
    label?: string | undefined;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: false | undefined;
}>;
export type LinkEntity = z.infer<typeof LinkEntity>;
export declare const TextEntity: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
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
}>;
export declare const TextAreaEntity: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
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
}>;
export declare const SelectCommonOptions: z.ZodObject<z.objectUtil.extendShape<{
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
export declare const SingleSelectEntity: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
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
}>;
export declare const MultipleSelectCommonOptions: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
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
}>, {
    delimiter: z.ZodOptional<z.ZodString>;
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
    delimiter?: string | undefined;
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
    delimiter?: string | undefined;
}>;
export declare const MultipleSelectEntity: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
    type: z.ZodString;
    field: z.ZodString;
    label: z.ZodString;
    help: z.ZodOptional<z.ZodString>;
    tooltip: z.ZodOptional<z.ZodString>;
}, {
    required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
}>, {
    type: z.ZodLiteral<"multipleSelect">;
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
    options: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
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
    }>, {
        delimiter: z.ZodOptional<z.ZodString>;
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
        delimiter?: string | undefined;
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
        delimiter?: string | undefined;
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
        delimiter?: string | undefined;
    };
    type: "multipleSelect";
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
        delimiter?: string | undefined;
    };
    type: "multipleSelect";
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
}>;
export declare const CheckboxEntity: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
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
}>;
export declare const CheckboxGroupEntity: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
    type: z.ZodString;
    field: z.ZodString;
    label: z.ZodString;
    help: z.ZodOptional<z.ZodString>;
    tooltip: z.ZodOptional<z.ZodString>;
}, {
    required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
}>, {
    type: z.ZodLiteral<"checkboxGroup">;
    validators: z.ZodOptional<z.ZodTuple<[z.ZodObject<{
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
    }>], null>>;
    defaultValue: z.ZodOptional<z.ZodUnion<[z.ZodNumber, z.ZodBoolean]>>;
    options: z.ZodObject<z.objectUtil.extendShape<{
        display: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        disableonEdit: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        enable: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        requiredWhenVisible: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
    }, {
        groups: z.ZodOptional<z.ZodArray<z.ZodObject<{
            label: z.ZodString;
            fields: z.ZodArray<z.ZodString, "many">;
            options: z.ZodOptional<z.ZodObject<{
                isExpandable: z.ZodOptional<z.ZodBoolean>;
                expand: z.ZodOptional<z.ZodBoolean>;
            }, "strip", z.ZodTypeAny, {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            }, {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }, {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }>, "many">>;
        rows: z.ZodArray<z.ZodObject<{
            field: z.ZodString;
            checkbox: z.ZodOptional<z.ZodObject<{
                label: z.ZodOptional<z.ZodString>;
                defaultValue: z.ZodOptional<z.ZodBoolean>;
            }, "strip", z.ZodTypeAny, {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            }, {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            }>>;
            input: z.ZodOptional<z.ZodObject<{
                defaultValue: z.ZodOptional<z.ZodNumber>;
                validators: z.ZodOptional<z.ZodTuple<[z.ZodObject<{
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
                }>], null>>;
                required: z.ZodOptional<z.ZodBoolean>;
            }, "strip", z.ZodTypeAny, {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            }, {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
            input?: {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            } | undefined;
        }, {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
            input?: {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            } | undefined;
        }>, "many">;
    }>, "strip", z.ZodTypeAny, {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
            input?: {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    }, {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
            input?: {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    }>;
}>, "strip", z.ZodTypeAny, {
    options: {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
            input?: {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    };
    type: "checkboxGroup";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: [{
        type: "regex";
        pattern: string;
        errorMsg?: string | undefined;
    }] | undefined;
    defaultValue?: number | boolean | undefined;
}, {
    options: {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
            input?: {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    };
    type: "checkboxGroup";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: [{
        type: "regex";
        pattern: string;
        errorMsg?: string | undefined;
    }] | undefined;
    defaultValue?: number | boolean | undefined;
}>;
export declare const CheckboxTreeEntity: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
    type: z.ZodString;
    field: z.ZodString;
    label: z.ZodString;
    help: z.ZodOptional<z.ZodString>;
    tooltip: z.ZodOptional<z.ZodString>;
}, {
    required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
}>, {
    type: z.ZodLiteral<"checkboxTree">;
    validators: z.ZodOptional<z.ZodTuple<[z.ZodObject<{
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
    }>], null>>;
    defaultValue: z.ZodOptional<z.ZodUnion<[z.ZodNumber, z.ZodBoolean]>>;
    options: z.ZodObject<z.objectUtil.extendShape<{
        display: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        disableonEdit: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        enable: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        requiredWhenVisible: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
    }, {
        groups: z.ZodOptional<z.ZodArray<z.ZodObject<{
            label: z.ZodString;
            fields: z.ZodArray<z.ZodString, "many">;
            options: z.ZodOptional<z.ZodObject<{
                isExpandable: z.ZodOptional<z.ZodBoolean>;
                expand: z.ZodOptional<z.ZodBoolean>;
            }, "strip", z.ZodTypeAny, {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            }, {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }, {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }>, "many">>;
        rows: z.ZodArray<z.ZodObject<{
            field: z.ZodString;
            checkbox: z.ZodOptional<z.ZodObject<{
                label: z.ZodOptional<z.ZodString>;
                defaultValue: z.ZodOptional<z.ZodBoolean>;
            }, "strip", z.ZodTypeAny, {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            }, {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
        }, {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
        }>, "many">;
    }>, "strip", z.ZodTypeAny, {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    }, {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    }>;
}>, "strip", z.ZodTypeAny, {
    options: {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    };
    type: "checkboxTree";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: [{
        type: "regex";
        pattern: string;
        errorMsg?: string | undefined;
    }] | undefined;
    defaultValue?: number | boolean | undefined;
}, {
    options: {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    };
    type: "checkboxTree";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: [{
        type: "regex";
        pattern: string;
        errorMsg?: string | undefined;
    }] | undefined;
    defaultValue?: number | boolean | undefined;
}>;
export declare const RadioEntity: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
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
}>;
export declare const FileEntity: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
    type: z.ZodString;
    field: z.ZodString;
    label: z.ZodString;
    help: z.ZodOptional<z.ZodString>;
    tooltip: z.ZodOptional<z.ZodString>;
}, {
    required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
}>, {
    type: z.ZodLiteral<"file">;
    defaultValue: z.ZodOptional<z.ZodString>;
    validators: z.ZodOptional<z.ZodArray<z.ZodUnion<[z.ZodObject<{
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
    }>]>, "many">>;
    options: z.ZodOptional<z.ZodObject<z.objectUtil.extendShape<{
        display: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        disableonEdit: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        enable: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        requiredWhenVisible: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
    }, {
        maxFileSize: z.ZodOptional<z.ZodNumber>;
        fileSupportMessage: z.ZodOptional<z.ZodString>;
        supportedFileTypes: z.ZodArray<z.ZodString, "many">;
        useBase64Encoding: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    }>, "strip", z.ZodTypeAny, {
        supportedFileTypes: string[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        maxFileSize?: number | undefined;
        fileSupportMessage?: string | undefined;
        useBase64Encoding?: boolean | undefined;
    }, {
        supportedFileTypes: string[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        maxFileSize?: number | undefined;
        fileSupportMessage?: string | undefined;
        useBase64Encoding?: boolean | undefined;
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
    type: "file";
    label: string;
    field: string;
    options?: {
        supportedFileTypes: string[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        maxFileSize?: number | undefined;
        fileSupportMessage?: string | undefined;
        useBase64Encoding?: boolean | undefined;
    } | undefined;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: ({
        type: "string";
        minLength: number;
        maxLength: number;
        errorMsg?: string | undefined;
    } | {
        type: "regex";
        pattern: string;
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
    type: "file";
    label: string;
    field: string;
    options?: {
        supportedFileTypes: string[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        maxFileSize?: number | undefined;
        fileSupportMessage?: string | undefined;
        useBase64Encoding?: boolean | undefined;
    } | undefined;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: ({
        type: "string";
        minLength: number;
        maxLength: number;
        errorMsg?: string | undefined;
    } | {
        type: "regex";
        pattern: string;
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
}>;
export declare const OAuthFields: z.ZodObject<{
    oauth_field: z.ZodString;
    label: z.ZodString;
    field: z.ZodString;
    type: z.ZodOptional<z.ZodDefault<z.ZodLiteral<"text">>>;
    help: z.ZodString;
    encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
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
}, "strip", z.ZodTypeAny, {
    label: string;
    field: string;
    help: string;
    oauth_field: string;
    options?: {
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    } | undefined;
    type?: "text" | undefined;
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
    label: string;
    field: string;
    help: string;
    oauth_field: string;
    options?: {
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    } | undefined;
    type?: "text" | undefined;
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
}>;
export declare const OAuthEntity: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
    type: z.ZodString;
    field: z.ZodString;
    label: z.ZodString;
    help: z.ZodOptional<z.ZodString>;
    tooltip: z.ZodOptional<z.ZodString>;
}, {
    required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
}>, {
    type: z.ZodLiteral<"oauth">;
    defaultValue: z.ZodOptional<z.ZodString>;
    validators: z.ZodOptional<z.ZodArray<z.ZodUnion<[z.ZodObject<{
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
    }>]>, "many">>;
    options: z.ZodObject<z.objectUtil.extendShape<Omit<{
        display: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        disableonEdit: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        enable: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        requiredWhenVisible: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
    }, "requiredWhenVisible">, {
        auth_type: z.ZodArray<z.ZodUnion<[z.ZodLiteral<"basic">, z.ZodLiteral<"oauth">]>, "many">;
        basic: z.ZodOptional<z.ZodArray<z.ZodObject<{
            oauth_field: z.ZodString;
            label: z.ZodString;
            field: z.ZodString;
            type: z.ZodOptional<z.ZodDefault<z.ZodLiteral<"text">>>;
            help: z.ZodString;
            encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
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
        }, "strip", z.ZodTypeAny, {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }>, "many">>;
        oauth: z.ZodOptional<z.ZodArray<z.ZodObject<{
            oauth_field: z.ZodString;
            label: z.ZodString;
            field: z.ZodString;
            type: z.ZodOptional<z.ZodDefault<z.ZodLiteral<"text">>>;
            help: z.ZodString;
            encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
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
        }, "strip", z.ZodTypeAny, {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }>, "many">>;
        auth_label: z.ZodOptional<z.ZodString>;
        oauth_popup_width: z.ZodOptional<z.ZodNumber>;
        oauth_popup_height: z.ZodOptional<z.ZodNumber>;
        oauth_timeout: z.ZodOptional<z.ZodNumber>;
        auth_code_endpoint: z.ZodOptional<z.ZodString>;
        access_token_endpoint: z.ZodOptional<z.ZodString>;
        oauth_state_enabled: z.ZodOptional<z.ZodBoolean>;
        auth_endpoint_token_access_type: z.ZodOptional<z.ZodString>;
    }>, "strip", z.ZodTypeAny, {
        auth_type: ("oauth" | "basic")[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        oauth?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        basic?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        auth_label?: string | undefined;
        oauth_popup_width?: number | undefined;
        oauth_popup_height?: number | undefined;
        oauth_timeout?: number | undefined;
        auth_code_endpoint?: string | undefined;
        access_token_endpoint?: string | undefined;
        oauth_state_enabled?: boolean | undefined;
        auth_endpoint_token_access_type?: string | undefined;
    }, {
        auth_type: ("oauth" | "basic")[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        oauth?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        basic?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        auth_label?: string | undefined;
        oauth_popup_width?: number | undefined;
        oauth_popup_height?: number | undefined;
        oauth_timeout?: number | undefined;
        auth_code_endpoint?: string | undefined;
        access_token_endpoint?: string | undefined;
        oauth_state_enabled?: boolean | undefined;
        auth_endpoint_token_access_type?: string | undefined;
    }>;
}>, "strip", z.ZodTypeAny, {
    options: {
        auth_type: ("oauth" | "basic")[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        oauth?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        basic?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        auth_label?: string | undefined;
        oauth_popup_width?: number | undefined;
        oauth_popup_height?: number | undefined;
        oauth_timeout?: number | undefined;
        auth_code_endpoint?: string | undefined;
        access_token_endpoint?: string | undefined;
        oauth_state_enabled?: boolean | undefined;
        auth_endpoint_token_access_type?: string | undefined;
    };
    type: "oauth";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: ({
        type: "string";
        minLength: number;
        maxLength: number;
        errorMsg?: string | undefined;
    } | {
        type: "regex";
        pattern: string;
        errorMsg?: string | undefined;
    })[] | undefined;
    defaultValue?: string | undefined;
}, {
    options: {
        auth_type: ("oauth" | "basic")[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        oauth?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        basic?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        auth_label?: string | undefined;
        oauth_popup_width?: number | undefined;
        oauth_popup_height?: number | undefined;
        oauth_timeout?: number | undefined;
        auth_code_endpoint?: string | undefined;
        access_token_endpoint?: string | undefined;
        oauth_state_enabled?: boolean | undefined;
        auth_endpoint_token_access_type?: string | undefined;
    };
    type: "oauth";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: ({
        type: "string";
        minLength: number;
        maxLength: number;
        errorMsg?: string | undefined;
    } | {
        type: "regex";
        pattern: string;
        errorMsg?: string | undefined;
    })[] | undefined;
    defaultValue?: string | undefined;
}>;
export declare const CustomEntity: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
    type: z.ZodString;
    field: z.ZodString;
    label: z.ZodString;
    help: z.ZodOptional<z.ZodString>;
    tooltip: z.ZodOptional<z.ZodString>;
}, {
    required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
}>, {
    type: z.ZodLiteral<"custom">;
    options: z.ZodObject<{
        type: z.ZodLiteral<"external">;
        src: z.ZodString;
        hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
    }, "strip", z.ZodTypeAny, {
        type: "external";
        src: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    }, {
        type: "external";
        src: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    }>;
}>, "strip", z.ZodTypeAny, {
    options: {
        type: "external";
        src: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    };
    type: "custom";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
}, {
    options: {
        type: "external";
        src: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    };
    type: "custom";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
}>;
export declare const SingleSelectSplunkSearchEntity: z.ZodObject<z.objectUtil.extendShape<{
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
}>;
export declare const AnyOfEntity: z.ZodDiscriminatedUnion<"type", [z.ZodObject<z.objectUtil.extendShape<{
    type: z.ZodString;
    field: z.ZodString;
    label: z.ZodString;
    help: z.ZodOptional<z.ZodString>;
    tooltip: z.ZodOptional<z.ZodString>;
}, {
    type: z.ZodLiteral<"helpLink">;
    label: z.ZodOptional<z.ZodString>;
    options: z.ZodObject<{
        text: z.ZodString;
        link: z.ZodString;
        hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
    }, "strip", z.ZodTypeAny, {
        text: string;
        link: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    }, {
        text: string;
        link: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    }>;
    required: z.ZodOptional<z.ZodDefault<z.ZodLiteral<false>>>;
}>, "strip", z.ZodTypeAny, {
    options: {
        text: string;
        link: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    };
    type: "helpLink";
    field: string;
    label?: string | undefined;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: false | undefined;
}, {
    options: {
        text: string;
        link: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    };
    type: "helpLink";
    field: string;
    label?: string | undefined;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: false | undefined;
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
    type: z.ZodLiteral<"multipleSelect">;
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
    options: z.ZodObject<z.objectUtil.extendShape<z.objectUtil.extendShape<{
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
    }>, {
        delimiter: z.ZodOptional<z.ZodString>;
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
        delimiter?: string | undefined;
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
        delimiter?: string | undefined;
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
        delimiter?: string | undefined;
    };
    type: "multipleSelect";
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
        delimiter?: string | undefined;
    };
    type: "multipleSelect";
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
    type: z.ZodLiteral<"checkboxGroup">;
    validators: z.ZodOptional<z.ZodTuple<[z.ZodObject<{
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
    }>], null>>;
    defaultValue: z.ZodOptional<z.ZodUnion<[z.ZodNumber, z.ZodBoolean]>>;
    options: z.ZodObject<z.objectUtil.extendShape<{
        display: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        disableonEdit: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        enable: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        requiredWhenVisible: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
    }, {
        groups: z.ZodOptional<z.ZodArray<z.ZodObject<{
            label: z.ZodString;
            fields: z.ZodArray<z.ZodString, "many">;
            options: z.ZodOptional<z.ZodObject<{
                isExpandable: z.ZodOptional<z.ZodBoolean>;
                expand: z.ZodOptional<z.ZodBoolean>;
            }, "strip", z.ZodTypeAny, {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            }, {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }, {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }>, "many">>;
        rows: z.ZodArray<z.ZodObject<{
            field: z.ZodString;
            checkbox: z.ZodOptional<z.ZodObject<{
                label: z.ZodOptional<z.ZodString>;
                defaultValue: z.ZodOptional<z.ZodBoolean>;
            }, "strip", z.ZodTypeAny, {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            }, {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            }>>;
            input: z.ZodOptional<z.ZodObject<{
                defaultValue: z.ZodOptional<z.ZodNumber>;
                validators: z.ZodOptional<z.ZodTuple<[z.ZodObject<{
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
                }>], null>>;
                required: z.ZodOptional<z.ZodBoolean>;
            }, "strip", z.ZodTypeAny, {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            }, {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
            input?: {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            } | undefined;
        }, {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
            input?: {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            } | undefined;
        }>, "many">;
    }>, "strip", z.ZodTypeAny, {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
            input?: {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    }, {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
            input?: {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    }>;
}>, "strip", z.ZodTypeAny, {
    options: {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
            input?: {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    };
    type: "checkboxGroup";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: [{
        type: "regex";
        pattern: string;
        errorMsg?: string | undefined;
    }] | undefined;
    defaultValue?: number | boolean | undefined;
}, {
    options: {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
            input?: {
                required?: boolean | undefined;
                validators?: [{
                    type: "number";
                    range: number[];
                    errorMsg?: string | undefined;
                    isInteger?: boolean | undefined;
                }] | undefined;
                defaultValue?: number | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    };
    type: "checkboxGroup";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: [{
        type: "regex";
        pattern: string;
        errorMsg?: string | undefined;
    }] | undefined;
    defaultValue?: number | boolean | undefined;
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
    type: z.ZodLiteral<"checkboxTree">;
    validators: z.ZodOptional<z.ZodTuple<[z.ZodObject<{
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
    }>], null>>;
    defaultValue: z.ZodOptional<z.ZodUnion<[z.ZodNumber, z.ZodBoolean]>>;
    options: z.ZodObject<z.objectUtil.extendShape<{
        display: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        disableonEdit: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        enable: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        requiredWhenVisible: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
    }, {
        groups: z.ZodOptional<z.ZodArray<z.ZodObject<{
            label: z.ZodString;
            fields: z.ZodArray<z.ZodString, "many">;
            options: z.ZodOptional<z.ZodObject<{
                isExpandable: z.ZodOptional<z.ZodBoolean>;
                expand: z.ZodOptional<z.ZodBoolean>;
            }, "strip", z.ZodTypeAny, {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            }, {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }, {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }>, "many">>;
        rows: z.ZodArray<z.ZodObject<{
            field: z.ZodString;
            checkbox: z.ZodOptional<z.ZodObject<{
                label: z.ZodOptional<z.ZodString>;
                defaultValue: z.ZodOptional<z.ZodBoolean>;
            }, "strip", z.ZodTypeAny, {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            }, {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
        }, {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
        }>, "many">;
    }>, "strip", z.ZodTypeAny, {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    }, {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    }>;
}>, "strip", z.ZodTypeAny, {
    options: {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    };
    type: "checkboxTree";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: [{
        type: "regex";
        pattern: string;
        errorMsg?: string | undefined;
    }] | undefined;
    defaultValue?: number | boolean | undefined;
}, {
    options: {
        rows: {
            field: string;
            checkbox?: {
                label?: string | undefined;
                defaultValue?: boolean | undefined;
            } | undefined;
        }[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        groups?: {
            label: string;
            fields: string[];
            options?: {
                isExpandable?: boolean | undefined;
                expand?: boolean | undefined;
            } | undefined;
        }[] | undefined;
    };
    type: "checkboxTree";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: [{
        type: "regex";
        pattern: string;
        errorMsg?: string | undefined;
    }] | undefined;
    defaultValue?: number | boolean | undefined;
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
    type: z.ZodLiteral<"file">;
    defaultValue: z.ZodOptional<z.ZodString>;
    validators: z.ZodOptional<z.ZodArray<z.ZodUnion<[z.ZodObject<{
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
    }>]>, "many">>;
    options: z.ZodOptional<z.ZodObject<z.objectUtil.extendShape<{
        display: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        disableonEdit: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        enable: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        requiredWhenVisible: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
    }, {
        maxFileSize: z.ZodOptional<z.ZodNumber>;
        fileSupportMessage: z.ZodOptional<z.ZodString>;
        supportedFileTypes: z.ZodArray<z.ZodString, "many">;
        useBase64Encoding: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
    }>, "strip", z.ZodTypeAny, {
        supportedFileTypes: string[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        maxFileSize?: number | undefined;
        fileSupportMessage?: string | undefined;
        useBase64Encoding?: boolean | undefined;
    }, {
        supportedFileTypes: string[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        maxFileSize?: number | undefined;
        fileSupportMessage?: string | undefined;
        useBase64Encoding?: boolean | undefined;
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
    type: "file";
    label: string;
    field: string;
    options?: {
        supportedFileTypes: string[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        maxFileSize?: number | undefined;
        fileSupportMessage?: string | undefined;
        useBase64Encoding?: boolean | undefined;
    } | undefined;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: ({
        type: "string";
        minLength: number;
        maxLength: number;
        errorMsg?: string | undefined;
    } | {
        type: "regex";
        pattern: string;
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
    type: "file";
    label: string;
    field: string;
    options?: {
        supportedFileTypes: string[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        requiredWhenVisible?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        maxFileSize?: number | undefined;
        fileSupportMessage?: string | undefined;
        useBase64Encoding?: boolean | undefined;
    } | undefined;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: ({
        type: "string";
        minLength: number;
        maxLength: number;
        errorMsg?: string | undefined;
    } | {
        type: "regex";
        pattern: string;
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
    type: z.ZodLiteral<"oauth">;
    defaultValue: z.ZodOptional<z.ZodString>;
    validators: z.ZodOptional<z.ZodArray<z.ZodUnion<[z.ZodObject<{
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
    }>]>, "many">>;
    options: z.ZodObject<z.objectUtil.extendShape<Omit<{
        display: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        disableonEdit: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        enable: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        requiredWhenVisible: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
        hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
    }, "requiredWhenVisible">, {
        auth_type: z.ZodArray<z.ZodUnion<[z.ZodLiteral<"basic">, z.ZodLiteral<"oauth">]>, "many">;
        basic: z.ZodOptional<z.ZodArray<z.ZodObject<{
            oauth_field: z.ZodString;
            label: z.ZodString;
            field: z.ZodString;
            type: z.ZodOptional<z.ZodDefault<z.ZodLiteral<"text">>>;
            help: z.ZodString;
            encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
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
        }, "strip", z.ZodTypeAny, {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }>, "many">>;
        oauth: z.ZodOptional<z.ZodArray<z.ZodObject<{
            oauth_field: z.ZodString;
            label: z.ZodString;
            field: z.ZodString;
            type: z.ZodOptional<z.ZodDefault<z.ZodLiteral<"text">>>;
            help: z.ZodString;
            encrypted: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
            required: z.ZodOptional<z.ZodDefault<z.ZodBoolean>>;
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
        }, "strip", z.ZodTypeAny, {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }>, "many">>;
        auth_label: z.ZodOptional<z.ZodString>;
        oauth_popup_width: z.ZodOptional<z.ZodNumber>;
        oauth_popup_height: z.ZodOptional<z.ZodNumber>;
        oauth_timeout: z.ZodOptional<z.ZodNumber>;
        auth_code_endpoint: z.ZodOptional<z.ZodString>;
        access_token_endpoint: z.ZodOptional<z.ZodString>;
        oauth_state_enabled: z.ZodOptional<z.ZodBoolean>;
        auth_endpoint_token_access_type: z.ZodOptional<z.ZodString>;
    }>, "strip", z.ZodTypeAny, {
        auth_type: ("oauth" | "basic")[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        oauth?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        basic?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        auth_label?: string | undefined;
        oauth_popup_width?: number | undefined;
        oauth_popup_height?: number | undefined;
        oauth_timeout?: number | undefined;
        auth_code_endpoint?: string | undefined;
        access_token_endpoint?: string | undefined;
        oauth_state_enabled?: boolean | undefined;
        auth_endpoint_token_access_type?: string | undefined;
    }, {
        auth_type: ("oauth" | "basic")[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        oauth?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        basic?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        auth_label?: string | undefined;
        oauth_popup_width?: number | undefined;
        oauth_popup_height?: number | undefined;
        oauth_timeout?: number | undefined;
        auth_code_endpoint?: string | undefined;
        access_token_endpoint?: string | undefined;
        oauth_state_enabled?: boolean | undefined;
        auth_endpoint_token_access_type?: string | undefined;
    }>;
}>, "strip", z.ZodTypeAny, {
    options: {
        auth_type: ("oauth" | "basic")[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        oauth?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        basic?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        auth_label?: string | undefined;
        oauth_popup_width?: number | undefined;
        oauth_popup_height?: number | undefined;
        oauth_timeout?: number | undefined;
        auth_code_endpoint?: string | undefined;
        access_token_endpoint?: string | undefined;
        oauth_state_enabled?: boolean | undefined;
        auth_endpoint_token_access_type?: string | undefined;
    };
    type: "oauth";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: ({
        type: "string";
        minLength: number;
        maxLength: number;
        errorMsg?: string | undefined;
    } | {
        type: "regex";
        pattern: string;
        errorMsg?: string | undefined;
    })[] | undefined;
    defaultValue?: string | undefined;
}, {
    options: {
        auth_type: ("oauth" | "basic")[];
        display?: boolean | undefined;
        disableonEdit?: boolean | undefined;
        enable?: boolean | undefined;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
        oauth?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        basic?: {
            label: string;
            field: string;
            help: string;
            oauth_field: string;
            options?: {
                display?: boolean | undefined;
                disableonEdit?: boolean | undefined;
                enable?: boolean | undefined;
                requiredWhenVisible?: boolean | undefined;
                hideForPlatform?: "cloud" | "enterprise" | undefined;
            } | undefined;
            type?: "text" | undefined;
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
        }[] | undefined;
        auth_label?: string | undefined;
        oauth_popup_width?: number | undefined;
        oauth_popup_height?: number | undefined;
        oauth_timeout?: number | undefined;
        auth_code_endpoint?: string | undefined;
        access_token_endpoint?: string | undefined;
        oauth_state_enabled?: boolean | undefined;
        auth_endpoint_token_access_type?: string | undefined;
    };
    type: "oauth";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
    validators?: ({
        type: "string";
        minLength: number;
        maxLength: number;
        errorMsg?: string | undefined;
    } | {
        type: "regex";
        pattern: string;
        errorMsg?: string | undefined;
    })[] | undefined;
    defaultValue?: string | undefined;
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
    type: z.ZodLiteral<"custom">;
    options: z.ZodObject<{
        type: z.ZodLiteral<"external">;
        src: z.ZodString;
        hideForPlatform: z.ZodOptional<z.ZodEnum<["cloud", "enterprise"]>>;
    }, "strip", z.ZodTypeAny, {
        type: "external";
        src: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    }, {
        type: "external";
        src: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    }>;
}>, "strip", z.ZodTypeAny, {
    options: {
        type: "external";
        src: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    };
    type: "custom";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
}, {
    options: {
        type: "external";
        src: string;
        hideForPlatform?: "cloud" | "enterprise" | undefined;
    };
    type: "custom";
    label: string;
    field: string;
    help?: string | undefined;
    tooltip?: string | undefined;
    required?: boolean | undefined;
    encrypted?: boolean | undefined;
}>]>;
