export default function AccountPlaceholder({
  title,
  description,
  items,
}: {
  title: string;
  description: string;
  items?: string[];
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-3">
      <h2 className="text-sm font-semibold text-gray-900">{title}</h2>
      <p className="text-sm text-gray-500">{description}</p>
      {items && items.length > 0 && (
        <ul className="space-y-1.5 pt-2">
          {items.map((item) => (
            <li key={item} className="flex items-center gap-2 text-sm text-gray-600">
              <span className="w-1.5 h-1.5 rounded-full bg-gray-300" />
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
