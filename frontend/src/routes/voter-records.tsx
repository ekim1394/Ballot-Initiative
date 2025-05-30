import DataFrameTable from "@/components/DataFrameTable/dataframetable";
import { createFileRoute } from "@tanstack/react-router";
import { FileInput } from "@/components/ui/fileinput";
import { useState } from "react";

export const Route = createFileRoute("/voter-records")({
  component: VoterRecord,
});

function VoterRecord() {
  const [voterRecords, setVoterRecords] = useState([]);
  return (
    <div className="text-left">
      <FileInput accept=".csv" id="voter_records" />
    </div>
  );
}
