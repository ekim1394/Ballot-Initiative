import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar, items } from "@/components/sidebar";
import { ModeToggle } from "./components/theme-provider/mode-toggle";
import { useLocation } from "@tanstack/react-router";
import { Toaster } from "@/components/ui/sonner";

export default function Layout({ children }: { children?: React.ReactNode }) {
  const location = useLocation();

  return (
    <SidebarProvider>
      <AppSidebar />
      <div className="flex flex-col h-screen w-screen">
        <header className="text-left flex">
          <SidebarTrigger /> | {""}
          {items.find((item) => item.url === location.pathname)?.title}
        </header>
        <main className="w-full mb-auto">
          {children}
          <ModeToggle />
          <Toaster />
        </main>
        <footer className="w-full centered">
          © 2024 Ballot Initiative Project
        </footer>
      </div>
    </SidebarProvider>
  );
}
