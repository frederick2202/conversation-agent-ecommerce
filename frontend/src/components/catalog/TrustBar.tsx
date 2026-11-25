import { BadgeCheck, Shield, Star, Truck } from "lucide-react";

export function TrustBar() {
  const items = [
    { icon: BadgeCheck, title: "+120 marcas oficiais", desc: "produtos lacrados com NF-e" },
    { icon: Shield, title: "Garantia de 12 meses", desc: "suporte especializado Lumen" },
    { icon: Truck, title: "Frete Grátis", desc: "acima de R$ 499 para todo Brasil" },
    { icon: Star, title: "Nota 4.9 / 5", desc: "avaliação verificada dos clientes" },
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 lg:px-8 -mt-4 relative z-10">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 rounded-xl bg-[#071124] border border-white/10 px-6 py-4 shadow-xl">
        {items.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="flex items-center gap-3">
            <Icon className="h-6 w-6 text-emerald-400 shrink-0" />
            <div>
              <p className="text-sm font-bold text-white">{title}</p>
              <p className="text-xs text-slate-400">{desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
