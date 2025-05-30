import { FileInput } from "@/components/ui/fileinput";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

export const Route = createFileRoute("/ballots")({
  component: RouteComponent,
});

function RouteComponent() {
  const [ballots, setBallots] = useState([]);
  return (
    <div className="text-left">
      <FileInput accept=".pdf" id="petition_signatures" />
    </div>
  );
}
