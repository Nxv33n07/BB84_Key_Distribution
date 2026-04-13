import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from "recharts";
import {
  Key,
  Shield,
  AlertTriangle,
  Copy,
  TrendingUp,
  CheckCircle,
  XCircle,
  ShieldCheck,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { ProtocolState } from "@/types/bb84";

interface ResultsCardProps {
  sharedKey: string;
  errorRate: number;
  isSecure: boolean;
  matchingBits: number;
  totalBits: number;
  errorHistory?: number[];
  rawAliceKey?: number[];
  rawBobKey?: number[];
  correctedBobKey?: number[];
  errorsFixed?: number;
  blocksWithErrors?: number;
  step: ProtocolState["step"];
}

export const ResultsCard = ({
  sharedKey,
  errorRate,
  isSecure,
  matchingBits,
  totalBits,
  errorHistory = [],
  rawAliceKey = [],
  rawBobKey = [],
  correctedBobKey = [],
  errorsFixed,
  blocksWithErrors,
  step,
}: ResultsCardProps) => {
  const { toast } = useToast();

  const copyKey = () => {
    navigator.clipboard.writeText(sharedKey);
    toast({
      title: "Key copied!",
      description: "Shared key copied to clipboard",
      duration: 2000,
    });
  };

  const chartData = errorHistory.map((rate, index) => ({
    round: index + 1,
    errorRate: rate * 100,
  }));

  const getSecurityStatus = () => {
    if (!sharedKey)
      return {
        text: "No key generated",
        variant: "secondary" as const,
        icon: null,
      };
    if (step === "complete")
      return {
        text: "Corrected",
        variant: "default" as const,
        icon: <CheckCircle className="w-4 h-4" />,
      };
    if (isSecure)
      return {
        text: "Secure",
        variant: "default" as const,
        icon: <CheckCircle className="w-4 h-4" />,
      };
    return {
      text: "Errors Found",
      variant: "destructive" as const,
      icon: <XCircle className="w-4 h-4" />,
    };
  };

  const securityStatus = getSecurityStatus();

  const showBitComparison = rawAliceKey.length > 0 && rawBobKey.length > 0;
  const showCorrected = step === "complete" && correctedBobKey.length > 0;

  return (
    <Card className="glass border-primary/30">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-primary">
          <Key className="w-5 h-5" />
          Quantum Key Distribution Results
          <Badge
            variant={securityStatus.variant}
            className="ml-auto flex items-center gap-1"
          >
            {securityStatus.icon}
            {securityStatus.text}
          </Badge>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Shared Key */}
        {sharedKey ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">
                {step === "complete"
                  ? "Corrected Shared Key"
                  : "Raw Key (Alice)"}
              </label>
              <Button
                size="sm"
                variant="outline"
                onClick={copyKey}
                className="h-7 text-xs"
              >
                <Copy className="w-3 h-3 mr-1" />
                Copy
              </Button>
            </div>
            <div className="p-3 bg-muted/50 rounded-lg font-mono text-sm break-all border">
              {sharedKey}
            </div>
          </div>
        ) : (
          <div className="text-center py-6 text-muted-foreground">
            <Key className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <div className="text-sm">
              Complete the protocol to generate a shared key
            </div>
          </div>
        )}

        {/* Bit-by-bit comparison — shown after Generate Key */}
        {showBitComparison && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-2 border rounded-lg p-3 bg-muted/20"
          >
            <label className="text-sm font-medium">
              Bit Comparison (Sifted Key)
            </label>
            <div className="space-y-1 font-mono text-xs overflow-x-auto">
              {/* Alice row */}
              <div className="flex items-center gap-1">
                <span className="w-12 text-muted-foreground shrink-0">
                  Alice:
                </span>
                <div className="flex gap-1 flex-wrap">
                  {rawAliceKey.map((bit, i) => (
                    <span
                      key={i}
                      className="w-5 h-5 flex items-center justify-center rounded text-white text-xs font-bold bg-blue-500"
                    >
                      {bit}
                    </span>
                  ))}
                </div>
              </div>
              {/* Bob row — mismatches in red */}
              <div className="flex items-center gap-1">
                <span className="w-12 text-muted-foreground shrink-0">
                  {showCorrected ? "Bob ✓:" : "Bob:"}
                </span>
                <div className="flex gap-1 flex-wrap">
                  {(showCorrected ? correctedBobKey : rawBobKey).map(
                    (bit, i) => {
                      const mismatch = bit !== rawAliceKey[i];
                      return (
                        <span
                          key={i}
                          className={`w-5 h-5 flex items-center justify-center rounded text-white text-xs font-bold ${
                            showCorrected
                              ? "bg-green-500"
                              : mismatch
                                ? "bg-destructive"
                                : "bg-green-500"
                          }`}
                        >
                          {bit}
                        </span>
                      );
                    },
                  )}
                </div>
              </div>
              {/* Match indicator row */}
              <div className="flex items-center gap-1">
                <span className="w-12 shrink-0" />
                <div className="flex gap-1 flex-wrap">
                  {rawAliceKey.map((bit, i) => {
                    const bobBit = showCorrected
                      ? correctedBobKey[i]
                      : rawBobKey[i];
                    const match = bobBit === bit;
                    return (
                      <span
                        key={i}
                        className="w-5 h-5 flex items-center justify-center text-xs"
                      >
                        {match ? (
                          <CheckCircle className="w-3 h-3 text-green-500" />
                        ) : (
                          <XCircle className="w-3 h-3 text-destructive" />
                        )}
                      </span>
                    );
                  })}
                </div>
              </div>
            </div>
            {!showCorrected && (
              <p className="text-xs text-muted-foreground">
                Red bits = mismatches. Press <strong>Fix Errors</strong> to
                correct them.
              </p>
            )}
          </motion.div>
        )}

        {/* Key Statistics */}
        {sharedKey && (
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-muted/30 rounded-lg">
              <div className="text-2xl font-bold text-primary">
                {sharedKey.length}
              </div>
              <div className="text-xs text-muted-foreground">Key Length</div>
            </div>
            <div className="text-center p-3 bg-muted/30 rounded-lg">
              <div className="text-2xl font-bold text-success">
                {matchingBits}
              </div>
              <div className="text-xs text-muted-foreground">Sifted Bits</div>
            </div>
            <div className="text-center p-3 bg-muted/30 rounded-lg">
              <div className="text-2xl font-bold text-muted-foreground">
                {totalBits}
              </div>
              <div className="text-xs text-muted-foreground">Total Sent</div>
            </div>
          </div>
        )}

        {/* Error Rate */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Quantum Bit Error Rate (QBER)
            </label>
            <span
              className={`text-sm font-mono ${
                errorRate > 0.11
                  ? "text-destructive"
                  : errorRate > 0.05
                    ? "text-warning"
                    : "text-success"
              }`}
            >
              {(errorRate * 100).toFixed(1)}%
            </span>
          </div>
          <Progress value={errorRate * 100} className="h-2" />
          <div className="text-xs text-muted-foreground">
            {errorRate > 0.11 ? (
              <div className="flex items-center gap-1 text-destructive">
                <AlertTriangle className="w-3 h-3" />
                High error rate suggests eavesdropping
              </div>
            ) : errorRate > 0.05 ? (
              <div className="text-warning">Moderate error rate detected</div>
            ) : (
              <div className="flex items-center gap-1 text-success">
                <Shield className="w-3 h-3" />
                Low error rate indicates secure channel
              </div>
            )}
          </div>
        </div>

        {/* Error Rate Chart */}
        {chartData.length > 1 && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Error Rate Trend</label>
            <div className="h-24 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <XAxis
                    dataKey="round"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 10 }}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 10 }}
                    domain={[0, 25]}
                  />
                  <Line
                    type="monotone"
                    dataKey="errorRate"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Error Correction Summary */}
        {errorsFixed !== undefined && step === "complete" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-1 border-t pt-3"
          >
            <label className="text-sm font-medium flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-green-500" />
              Error Correction Result
            </label>
            {errorsFixed === 0 ? (
              <p className="text-xs text-success">
                No errors found — key was already consistent
              </p>
            ) : (
              <p className="text-xs text-success">
                {errorsFixed} bit(s) corrected across {blocksWithErrors}{" "}
                block(s) — key is now consistent
              </p>
            )}
          </motion.div>
        )}

        {/* Protocol Explanation */}
        <div className="text-xs text-muted-foreground space-y-1 border-t pt-3">
          <div>
            • Error rates below 5% typically indicate secure transmission
          </div>
          <div>• Error rates above 11% suggest possible eavesdropping</div>
          <div>
            • Only bits measured with matching bases form the shared key
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
