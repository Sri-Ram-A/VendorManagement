"use client";

import * as React from "react";
import {
    ThemeProvider as NextThemesProvider,
    type ThemeProviderProps,
} from "next-themes";

import { TooltipProvider } from "@/components/ui/tooltip";

interface Props extends ThemeProviderProps {
    children: React.ReactNode;
}

export function ThemeProvider({ children, ...props }: Props) {
    return (
        <NextThemesProvider {...props}>
            <TooltipProvider delayDuration={0}>
                {children}
            </TooltipProvider>
        </NextThemesProvider>
    );
}